import requests
import json
import argparse


class WifiAgent:
    """
    A Python agent to interact with a local LLM API for Wi-Fi tool calling.
    """

    def __init__(self, llm_url="http://localhost:11434"):
        # Ensure the URL has proper scheme
        if not llm_url.startswith(("http://", "https://")):
            llm_url = f"http://{llm_url}"

        self.llm_url = llm_url.rstrip("/")
        print(f"WifiAgent initialized. Connecting to: {self.llm_url}")

    def _send_request(self, endpoint, payload):
        # Ensure endpoint starts with /
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"

        url = f"{self.llm_url}{endpoint}"
        headers = {"Content-Type": "application/json"}

        print(f"DEBUG: Making request to: {url}")  # Debug line

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            print(f"Error: Could not connect to LLM server at {url}.")
            print("Please ensure Ollama is running. Try: ollama serve")
            return None
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            if hasattr(response, "text"):
                print(f"Response: {response.text}")
            return None
        except requests.exceptions.RequestException as req_err:
            print(f"An unexpected request error occurred: {req_err}")
            return None
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON response from {url}")
            if hasattr(response, "text"):
                print(f"Response: {response.text}")
            return None

    def chat_with_tools(self, model, messages, tools=None, stream=False, options=None):
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if tools:
            payload["tools"] = tools
        if options:
            payload["options"] = options

        print(f"\n--- Sending chat_with_tools request to model: {model} ---")
        response_data = self._send_request("/api/chat", payload)
        return response_data


def call_real_wifi_tool(tool_name, tool_args, wifi_server_url):
    print(f"\n[Agent]: Calling Wi-Fi tool: {tool_name} with args: {tool_args}")
    try:
        response = requests.post(
            f"{wifi_server_url}/execute",
            json={"tool_name": tool_name, "tool_args": tool_args},
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to Wi-Fi server at {wifi_server_url}.")
        print("Please ensure your Wi-Fi server is running and accessible.")
        return {
            "status": "error",
            "message": f"Could not connect to Wi-Fi server at {wifi_server_url}",
        }
    except requests.exceptions.HTTPError as http_err:
        print(f"Wi-Fi HTTP error occurred: {http_err} - Response: {response.text}")
        return {
            "status": "error",
            "message": f"Wi-Fi HTTP error: {http_err} - {response.text}",
        }
    except Exception as e:
        print(f"An unexpected error occurred while calling Wi-Fi tool: {e}")
        return {
            "status": "error",
            "message": f"An error occurred calling Wi-Fi tool: {e}",
        }


def get_wifi_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "scan_wifi",
                "description": "Scan for available Wi-Fi networks",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "interface": {
                            "type": "string",
                            "description": "Wi-Fi interface (optional)",
                        }
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_wifi_status",
                "description": "Get current Wi-Fi connection status",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "interface": {
                            "type": "string",
                            "description": "Wi-Fi interface (optional)",
                        }
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_signal_strength",
                "description": "Get signal strength and quality metrics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "interface": {
                            "type": "string",
                            "description": "Wi-Fi interface (optional)",
                        }
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_interfaces",
                "description": "List all available network interfaces",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    ]


TOOLS_AVAILABLE = get_wifi_tools()


def main():
    parser = argparse.ArgumentParser(description="Wi-Fi Agent CLI")
    parser.add_argument(
        "--llm-url", default="http://localhost:11434", help="LLM API URL"
    )
    parser.add_argument("--model", default="llama3.1:8b", help="LLM model name")
    parser.add_argument(
        "--wifi-server-url", default="http://localhost:8080", help="Wi-Fi server URL"
    )
    parser.add_argument(
        "--output-file", default=None, help="Write conversation to this file"
    )
    args = parser.parse_args()

    llm_url = args.llm_url
    llm_model = args.model
    wifi_server_url = args.wifi_server_url
    output_file = args.output_file

    agent = WifiAgent(llm_url=llm_url)

    print("\n--- Starting Conversation with Tool-Enabled Wi-Fi Agent ---")
    print(
        "Try asking about Wi-Fi: 'Scan for networks', 'What is my Wi-Fi status?', 'List network interfaces'."
    )
    print("Type 'exit' to quit.")

    conversation_history = []
    conversation_log = []

    while True:
        user_input = input("\nUser: ")
        if user_input.lower() == "exit":
            break

        conversation_history.append({"role": "user", "content": user_input})
        conversation_log.append({"role": "user", "content": user_input})

        llm_response = agent.chat_with_tools(
            llm_model, conversation_history, tools=TOOLS_AVAILABLE
        )

        if not llm_response:
            print("[Agent]: Failed to get a response from LLM.")
            conversation_history.pop()
            continue

        response_message = llm_response.get("message", {})
        content = response_message.get("content", "")
        tool_calls = response_message.get("tool_calls")

        if tool_calls:
            print("[Agent]: LLM wants to call a tool!")
            conversation_history.append(response_message)
            conversation_log.append({"role": "assistant", "content": response_message})

            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                tool_args = tool_call["function"]["arguments"]

                tool_output = call_real_wifi_tool(tool_name, tool_args, wifi_server_url)
                print(f"[Agent]: Tool '{tool_name}' returned: {tool_output}")

                tool_history_entry = {
                    "role": "tool",
                    "content": json.dumps(tool_output),
                }
                if "id" in tool_call:
                    tool_history_entry["tool_call_id"] = tool_call["id"]
                conversation_history.append(tool_history_entry)
                conversation_log.append(tool_history_entry)

                final_llm_response = agent.chat_with_tools(
                    llm_model, conversation_history, tools=TOOLS_AVAILABLE
                )
                if final_llm_response and final_llm_response.get("message", {}).get(
                    "content"
                ):
                    final_content = final_llm_response["message"]["content"]
                    print(f"Assistant: {final_content}")
                    conversation_history.append(
                        {"role": "assistant", "content": final_content}
                    )
                    conversation_log.append(
                        {"role": "assistant", "content": final_content}
                    )
                else:
                    print(
                        "[Agent]: LLM did not provide a clear final response after tool execution."
                    )
                    print(f"Assistant (raw tool output): {tool_output}")
                    conversation_log.append(
                        {"role": "assistant", "content": str(tool_output)}
                    )
        else:
            if content:
                print(f"Assistant: {content}")
                conversation_history.append({"role": "assistant", "content": content})
                conversation_log.append({"role": "assistant", "content": content})
            else:
                print("[Agent]: LLM did not provide a direct response.")
                print(f"Assistant (raw response): {llm_response}")
                conversation_log.append(
                    {"role": "assistant", "content": str(llm_response)}
                )

    if output_file:
        try:
            with open(output_file, "w") as f:
                json.dump(conversation_log, f, indent=2)
            print(f"\nConversation written to {output_file}")
        except Exception as e:
            print(f"Failed to write conversation to file: {e}")


if __name__ == "__main__":
    main()
