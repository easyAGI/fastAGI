from datetime import datetime
import ujson as json
import os
import logging
from nicegui import ui  # Importing ui from nicegui

def display_internal_conclusion(openmind_instance, conclusion):
    """
    Display internal reasoning conclusion in the response window and log it to a JSON file
    """
    if conclusion not in ["No premises available for logic as conclusion", "No conclusion available"]:
        if openmind_instance.message_container.client.connected:
            with openmind_instance.message_container:
                response_message = ui.chat_message(name='intr', sent=False)
                response_message.clear()
                with response_message:
                    ui.html(f"{conclusion}")
        logging.info(f"Internal reasoning conclusion: {conclusion}")

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "conclusion": conclusion
        }

        log_file_path = "./memory/logs/thoughts.json"
        if not os.path.exists(log_file_path):
            with open(log_file_path, 'w') as file:
                json.dump([log_entry], file, indent=4)
        else:
            with open(log_file_path, 'r+') as file:
                data = json.load(file)
                data.append(log_entry)
                file.seek(0)
                json.dump(data, file, indent=4)

        with open('./memory/logs/conclusions.txt', 'a') as file:
            file.write(f"{datetime.now().isoformat()}: {conclusion}\n")

def display_all_premises(openmind_instance, premises):
    """
    Display all premises in the response window and log them to JSON files
    """
    for premise in premises:
        if premise and premise != "No premises available":
            if openmind_instance.message_container.client.connected:
                with openmind_instance.message_container:
                    response_message = ui.chat_message(name='premise', sent=False)
                    response_message.clear()
                    with response_message:
                        ui.html(f"{premise}")
            logging.info(f"Internal reasoning premise: {premise}")

            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "premise": premise
            }

            log_file_path = "./memory/logs/premises.json"
            if not os.path.exists(log_file_path):
                with open(log_file_path, 'w') as file:
                    json.dump([log_entry], file, indent=4)
            else:
                with open(log_file_path, 'r+') as file:
                    data = json.load(file)
                    if isinstance(data, dict):
                        data = [data]
                    data.append(log_entry)
                    file.seek(0)
                    json.dump(data, file, indent=4)

            with open('./memory/logs/premises.txt', 'a') as file:
                file.write(f"{datetime.now().isoformat()}: {premise}\n")

def display_all_thoughts(openmind_instance, thoughts):
    """
    Display all thoughts in the response window and log them to JSON files
    """
    for thought in thoughts:
        if thought and thought != "No thoughts available":
            if openmind_instance.message_container.client.connected:
                with openmind_instance.message_container:
                    response_message = ui.chat_message(name='thought', sent=False)
                    response_message.clear()
                    with response_message:
                        ui.html(f"{thought}")
            logging.info(f"Internal reasoning thought: {thought}")

            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "thought": thought
            }

            log_file_path = "./memory/logs/thoughts.json"
            if not os.path.exists(log_file_path):
                with open(log_file_path, 'w') as file:
                    json.dump([log_entry], file, indent=4)
            else:
                with open(log_file_path, 'r+') as file:
                    data = json.load(file)
                    if isinstance(data, dict):
                        data = [data]
                    data.append(log_entry)
                    file.seek(0)
                    json.dump(data, file, indent=4)

            with open('./memory/logs/thoughts.txt', 'a') as file:
                file.write(f"{datetime.now().isoformat()}: {thought}\n")

def display_all_decisions(openmind_instance, decisions):
    """
    Display all decisions in the response window and log them to JSON files
    """
    for decision in decisions:
        if decision and decision != "No decisions available":
            if openmind_instance.message_container.client.connected:
                with openmind_instance.message_container:
                    response_message = ui.chat_message(name='decision', sent=False)
                    response_message.clear()
                    with response_message:
                        ui.html(f"{decision}")
            logging.info(f"Internal reasoning decision: {decision}")

            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "decision": decision
            }

            log_file_path = "./memory/logs/decisions.json"
            if not os.path.exists(log_file_path):
                with open(log_file_path, 'w') as file:
                    json.dump([log_entry], file, indent=4)
            else:
                with open(log_file_path, 'r+') as file:
                    data = json.load(file)
                    if isinstance(data, dict):
                        data = [data]
                    data.append(log_entry)
                    file.seek(0)
                    json.dump(data, file, indent=4)

            with open('./memory/logs/decisions.txt', 'a') as file:
                file.write(f"{datetime.now().isoformat()}: {decision}\n")

