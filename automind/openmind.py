import os
import time
from datetime import datetime
from nicegui import ui  # importing ui for easyAGI
from memory.memory import create_memory_folders, store_in_stm, save_conversation_memory, save_internal_reasoning, DialogEntry, save_valid_truth
from webmind.ollama_handler import OllamaHandler  # Import OllamaHandler for modular Ollama interactions
from automind.automind import FundamentalAGI
from webmind.chatter import GPT4o, GroqModel, TogetherModel
from webmind.api import APIManager
import ujson  # Use the ujson module
import asyncio
import logging
import httpx

from automind.display_helpers import display_internal_conclusion, display_all_premises, display_all_thoughts, display_all_decisions

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class OpenMind:
    def __init__(self):
        self.api_manager = APIManager()
        self.agi_instance = None
        self.initialize_memory()
        self.message_container = ui.column()
        self.ollama_handler = OllamaHandler()  # initialize OllamaHandler instance
        self.internal_queue = asyncio.Queue()
        self.prompt = ""  # Initialize an empty prompt field
        self.keys_container = ui.column()  # initialize keys_container
        self.log = None  # placeholder for log
        self.initialization_warning_shown = False
        self.autonomous_reasoning = False  # Default autonomous reasoning to False

    def initialize_memory(self):
        create_memory_folders()

    def use_api_key(self, service, key):
        self.api_manager.api_keys[service] = key
        self.initialize_agi()
        if self.message_container.client.connected:
            with self.message_container:
                ui.notify(f'Using API key for {service}', type='positive')
        logging.info(f'Using API key for {service}')

    def add_api_key(self):
        service = self.service_input.value.strip()
        api_key = self.key_input.value.strip()
        logging.debug(f"Adding API key for {service}: {api_key[:4]}...{api_key[-4:]}")
        if service and api_key:
            self.api_manager.api_keys[service] = api_key
            self.api_manager.save_api_key(service, api_key)
            self.initialize_agi()
            if self.message_container.client.connected:
                ui.notify(f'API key for {service} added and loaded successfully')
            self.service_input.value = ''
            self.key_input.value = ''
            ui.run_javascript('setTimeout(() => { window.location.href = "/"; }, 1000);')
        else:
            ui.notify('Provide both service name and API key')

    def delete_api_key(self, service):
        logging.debug(f"Deleting API key for {service}")
        if service in self.api_manager.api_keys:
            del self.api_manager.api_keys[service]
            self.api_manager.remove_api_key(service)
            self.initialize_agi()
            if self.message_container.client.connected:
                ui.notify(f'API key for {service} removed successfully')
            self.list_api_keys()  # Refresh the list after deletion
        else:
            ui.notify(f'No API key found for {service}')

    def list_api_keys(self):
        if self.api_manager.api_keys:
            keys_list = [(service, key) for service, key in self.api_manager.api_keys.items()]
            logging.debug(f"Stored API keys: {keys_list}")
            if self.keys_container.client.connected:
                self.keys_container.clear()
                for service, key in keys_list:
                    with self.keys_container:
                        ui.label(f"{service}: {key[:4]}...{key[-4:]}").classes('flex-1')
                        ui.button('Delete', on_click=lambda s=service: self.delete_api_key(s)).classes('ml-4')
                ui.notify('Stored API keys:\n' + "\n".join([f"{service}: {key[:4]}...{key[-4:]}" for service, key in keys_list]))
        else:
            if self.keys_container.client.connected:
                ui.notify('No API keys in storage')
                self.keys_container.clear()
                with self.keys_container:
                    ui.label('No API keys in storage')

    def select_model(self, model_name):
        if model_name == 'openai':
            openai_key = self.api_manager.get_api_key('openai')
            if openai_key:
                chatter = GPT4o(openai_key)
                self.agi_instance = FundamentalAGI(chatter)
                if self.message_container.client.connected:
                    with self.message_container:
                        ui.notify('Using OpenAI for AGI')
                logging.debug("AGI initialized with OpenAI")
            else:
                if self.message_container.client.connected:
                    with self.message_container:
                        ui.notify('OpenAI API key not found. Please add the key first.', type='negative')
                logging.warning("OpenAI API key not found")
        elif model_name == 'groq':
            groq_key = self.api_manager.get_api_key('groq')
            if groq_key:
                chatter = GroqModel(groq_key)
                self.agi_instance = FundamentalAGI(chatter)
                if self.message_container.client.connected:
                    with self.message_container:
                        ui.notify('Using Groq for AGI')
                logging.debug("AGI initialized with Groq")
            else:
                if self.message_container.client.connected:
                    with self.message_container:
                        ui.notify('Groq API key not found. Please add the key first.', type='negative')
                logging.warning("Groq API key not found.")
        elif model_name == 'together':
            together_key = self.api_manager.get_api_key('together')
            if together_key:
                chatter = TogetherModel(together_key)
                self.agi_instance = FundamentalAGI(chatter)
                if self.message_container.client.connected:
                    with self.message_container:
                        ui.notify('Using Together AI for AGI')
                logging.debug("AGI initialized with Together AI")
            else:
                if self.message_container.client.connected:
                    with self.message_container:
                        ui.notify('Together AI API key not found. Please add the key first.', type='negative')
                logging.warning("Together AI API key not found")
        else:
            if self.message_container.client.connected:
                with self.message_container:
                    ui.notify(f'Using {model_name} for AGI')
            logging.debug(f"AGI initialized with {model_name}")

    def initialize_agi(self):
        openai_key = self.api_manager.get_api_key('openai')
        groq_key = self.api_manager.get_api_key('groq')
        together_key = self.api_manager.get_api_key('together')
        llama_running = self.check_llama_running()

        if openai_key:
            chatter = GPT4o(openai_key)
            self.agi_instance = FundamentalAGI(chatter)
            if self.message_container.client.connected:
                with self.message_container:
                    ui.notify('Using OpenAI for ezAGI')
            logging.debug("AGI initialized with OpenAI")
        elif groq_key:
            chatter = GroqModel(groq_key)
            self.agi_instance = FundamentalAGI(chatter)
            if self.message_container.client.connected:
                with self.message_container:
                    ui.notify('Using Groq for ezAGI')
            logging.debug("AGI initialized with Groq")
        elif together_key:
            chatter = TogetherModel(together_key)
            self.agi_instance = FundamentalAGI(chatter)
            if self.message_container.client.connected:
                with self.message_container:
                    ui.notify('Using Together AI for ezAGI')
            logging.debug("AGI initialized with Together AI")
        elif llama_running:
            # Call ollama_handler to list models when LLaMA is found running
            models = self.ollama_handler.list_models()
            if models:
                model_list = ", ".join(models)
                if self.message_container.client.connected:
                    with self.message_container:
                        ui.notify(f'LLaMA found running. Models available: {model_list}')
                logging.debug(f"LLaMA running on localhost:11434. Models available: {model_list}")
            else:
                if self.message_container.client.connected:
                    with self.messages_container:
                        ui.notify('LLaMA found running, but no models are available.')
                logging.debug("LLaMA running on localhost:11434, but no models are available")
        else:
            self.agi_instance = None
            if not self.initialization_warning_shown:
                if self.message_container.client.connected:
                    with self.message_container:
                        ui.notify('No valid API key or LLaMA instance found. Please add an API key or start LLaMA.')
                logging.debug("No valid API key or LLaMA instance found. AGI not initialized")
                self.initialization_warning_shown = True

    def check_llama_running(self):
        try:
            response = httpx.get('http://localhost:11434')
            if response.status_code == 200:
                return True
        except httpx.RequestError as e:
            logging.debug(f"LLaMA connection failed: {e}")
        return False

    async def get_conclusion_from_agi(self, prompt):
        """
        Get a conclusion from the AGI based on the provided prompt
        This method is asynchronous to allow non-blocking operations
        """
        if self.agi_instance is None:
            return "AGI not initialized. Please add an API key or start LLaMA"
        conclusion, thoughts = await asyncio.get_event_loop().run_in_executor(None, self.agi_instance.get_conclusion_from_agi, prompt)
        return conclusion, thoughts

    def display_premises(self):
        """
        Display premises in the response window
        """
        if self.message_container.client.connected:
            with self.message_container:
                with open('./memory/logs/premises.json', 'r') as file:
                    try:
                        premises = ujson.load(file)
                        for premise in premises:
                            ui.chat_message(text=premise, name='premise', sent=False)
                    except ujson.JSONDecodeError as e:
                        logging.error(f"Error loading premises: {e}")
                        ui.notify(f"Error loading premises: {e}", type='negative')

    def display_truth(self):
        """
        Display truth in the response window
        """
        if self.message_container.client.connected:
            with self.message_container:
                with open('./memory/logs/truth.json', 'r') as file:
                    try:
                        truth = ujson.load(file)
                        for truth_entry in truth:
                            ui.chat_message(text=truth_entry['truth'], name='truth', sent=False)
                    except ujson.JSONDecodeError as e:
                        logging.error(f"Error loading truth: {e}")
                        ui.notify(f"Error loading truth: {e}", type='negative')

    def display_thoughts(self, thoughts):
        """
        Display thoughts in the response window
        """
        if self.message_container.client.connected:
            with self.message_container:
                for thought in thoughts:
                    ui.chat_message(text=thought, name='thought', sent=False)

    def communicate_response(self, conclusion, thoughts):
        """
        Log and print the internal conclusion from reasoning
        """
        display_internal_conclusion(self, conclusion)
        self.display_premises()
        self.display_truth()
        self.display_thoughts(thoughts)
        return conclusion

    async def reasoning_loop(self):
        """
        Internal reasoning loop for continuous AGI reasoning without user interaction
        Adding a prompt to AGI processing its conclusion periodically
        The conclusions are currently displayed in the response window and saved to ./memory/logs/thoughts.json including ./memory/logs/notpremise.json
        """
        while True:
            if self.autonomous_reasoning:
                if self.agi_instance is None:
                    openai_key = self.api_manager.get_api_key('openai')
                    groq_key = self.api_manager.get_api_key('groq')
                    together_key = self.api_manager.get_api_key('together')
                    llama_running = self.check_llama_running()
                    if openai_key or groq_key or together_key or llama_running:
                        self.initialize_agi()
                    else:
                        if not self.initialization_warning_shown:
                            logging.debug("Waiting for API key or LLaMA instance...")
                            if self.message_container.client.connected:
                                with self.message_container:
                                    ui.notify('AGI not initialized. Add an API key or start LLaMA.')
                            self.initialization_warning_shown = True
                        await asyncio.sleep(30)  # Wait before checking again
                        continue

                prompt = self.prompt  # Use the updated prompt from user input
                conclusion, thoughts = await self.get_conclusion_from_agi(prompt)
                self.communicate_response(conclusion, thoughts)
                save_internal_reasoning({"timestamp": int(time.time()), "prompt": prompt, "conclusion": conclusion})
                if self.message_container.client.connected:
                    with self.message_container:
                        ui.notify('Reasoning loop conclusion saved')

                await asyncio.sleep(10)  # Adjust the delay as necessary
            else:
                await asyncio.sleep(1)  # Sleep briefly if autonomous reasoning is disabled

    async def main_loop(self):
        """
        Main loop to handle both internal reasoning and user input
        """
        reasoning_task = asyncio.create_task(self.reasoning_loop())
        reasoning_task.add_done_callback(self._handle_task_result)

        while True:
            prompt = await self.internal_queue.get()
            if prompt == 'exit':
                break
            self.prompt = prompt  # Update the prompt with the new input
            conclusion, thoughts = await self.get_conclusion_from_agi(prompt)
            self.communicate_response(conclusion, thoughts)
            # Save the input-response pair using save_conversation_memory
            save_conversation_memory({"dialog": {"instruction": prompt, "response": conclusion}})

    async def send_message(self, question):
        if self.message_container.client.connected:
            with self.message_container:
                ui.chat_message(text=question, name='query', sent=True)
                response_message = ui.chat_message(name='ezAGI', sent=False)
                spinner = ui.spinner(type='dots')

        try:
            conclusion, thoughts = await self.get_conclusion_from_agi(question)
            self.communicate_response(conclusion, thoughts)  # Display conclusion and reasoning details

            if response_message and self.message_container.client.connected:
                response_message.clear()
                with response_message:
                    ui.html(conclusion)

            await self.run_javascript_with_retry('window.scrollTo(0, document.body.scrollHeight)', retries=3, timeout=30.1)

            # Store the dialog entry
            entry = DialogEntry(question, conclusion)
            store_in_stm(entry)
            # Saves conversation following each input response to ./memory/stm/timestampmemory.json from memory.py
            save_conversation_memory({"dialog": {"instruction": question, "response": conclusion}})
        except Exception as e:
            logging.error(f"Error getting conclusion from easyAGI: {e}")
            if self.log:
                self.log.push(f"Error getting conclusion from easyAGI: {e}")
        finally:
            try:
                if self.message_container.client.connected:
                    self.message_container.remove(spinner)  # Correctly remove the spinner
            except KeyError:
                logging.warning("Spinner element not found in message_container")

    async def run_javascript_with_retry(self, script, retries=5, timeout=12.0):
        for attempt in range(retries):
            task = asyncio.create_task(ui.run_javascript(script, timeout=timeout))
            task.add_done_callback(self._handle_task_result)
            try:
                await task
                return
            except TimeoutError:
                logging.warning(f"JavaScript did not respond within {timeout} s on attempt {attempt + 1}")
        raise TimeoutError(f"JavaScript did not respond after {retries} attempts")

    def _handle_task_result(self, task: asyncio.Task) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            pass  # Task cancellation should not be logged as an error.
        except Exception as e:
            logging.exception('Exception raised by task = %r', task)

    def read_log_file(self, file_path):
        """
        Read the content of a log file and return it
        """
        try:
            with open(file_path, 'r') as file:
                return file.read()
        except FileNotFoundError:
            logging.error(f"Log file not found: {file_path}")
            return f"Log file not found: {file_path}"
        except Exception as e:
            logging.error(f"Error reading log file {file_path}: {e}")
            return f"Error reading log file {file_path}: {e}"

    def handle_javascript_response(self, msg):
        request_id = msg.get('request_id')
        result = msg.get('result', None)

        if request_id is not None:
            if result is not None:
                JavaScriptRequest.resolve(request_id, result)
            else:
                # Handle the case where 'result' is missing
                JavaScriptRequest.reject(request_id, 'Missing result in JavaScript response')
                logging.error(f"JavaScript response missing 'result' for request_id: {request_id}. Response: {msg}")
        else:
            # Handle the case where 'request_id' is missing if needed
            logging.error(f"JavaScript response missing 'request_id'. Response: {msg}")

        # Log the entire message for debugging purposes
        logging.debug(f"Received JavaScript response: {msg}")

if __name__ == "__main__":
    openmind = OpenMind()
    ui.run()

