from flask import Flask, request, jsonify
from flask_cors import cross_origin
from pathlib import Path
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
key = os.getenv("UPDATE_KEY")
ephemeris = None
varFilePath = Path("newRefTimes.json")


@app.route("/update-variables", methods=["POST"])
@cross_origin()  # Enables CORS specifically for this route
def receive_data():
    """Recieves messages from an outside script via an http request and updates
    an intermediary file that contains information that parsed by other functions
    in order to update the orb variables
    """
    authKey = request.headers.get("Authorization")
    if authKey != key:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    print("Received data:", data)
    try:
        if validateData(data["vars"]):
            updateData(data["vars"], varFile=varFilePath)
    except AttributeError:
        return jsonify({"status": "error", "message": "Bad Payload"}), 400

    return jsonify({"status": "success", "message": "Data received successfully"}), 200


def validateData(vars: dict) -> bool:
    """Does an initial screen of the data received from the http message.

    Parameters
    ---------
        vars: `dict`
            A `dict` containing keys that correspond to the orb names and values that are timestamps
            at which an event happened with that orb that can be used to calibrate it's position

    Returns:
    ---------
        `bool`
            True if vars argument contains valid keys and the correct type of value
    """
    for var in vars:
        if (
            var
            not in [
                "white",
                "black",
                "green",
                "red",
                "purple",
                "yellow",
                "cyan",
                "blue",
            ]
            or type(vars[var][0]) != int
            or type(vars[var][1]) != int
        ):
            return False
    return True


def updateData(vars, varFile: Path) -> None:
    variables = getVariables(varFile)
    print("variables:", variables)
    for var in vars:
        variables[var] = vars[var]
    updateVariables(vars, varFile)


def updateVariables(vars, variablesFile: Path) -> None:
    json_object = json.dumps(vars, indent=4)
    with variablesFile.open("w") as outfile:
        outfile.write(json_object)


def getVariables(variablesFile: Path) -> dict:
    variables = {}
    with variablesFile.open("r") as json_file:
        variables = json.load(json_file)
    return variables


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)  # Runs on http://<server-ip>:5000
