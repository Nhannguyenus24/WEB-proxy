# Proxy Server with Caching

This repository contains a simple Python proxy server implementation with caching capabilities. The proxy server can intercept HTTP requests from clients, communicate with the requested web servers, and cache responses for faster subsequent access.

## Features

- Supports GET, POST, HEAD requests and `--HEAD` method.
- Implements basic caching of responses to improve performance.
- Provides white-listing of allowed domains for access.
- Implements time-based access restrictions.
- Handles DNS resolution and forwards requests to appropriate web servers.
- Uses multithreading to handle multiple client connections simultaneously.

## Dependencies

This project requires the following Python modules:

- `socket`: For creating socket connections.
- `threading`: For managing concurrent connections.
- `time`: For time-related operations.
- `os`: For interacting with the file system.
- `sys`: For system-specific functionality.
- `configparser`: For reading configuration files.
- `shutil`: For file and directory operations.

## Configuration

The proxy server's behavior can be configured using the `config.ini` file. It allows you to set cache timeout, whitelist of allowed domains, and time-based access restrictions.

## Usage

1. Clone this repository to your local machine.
2. Modify the `config.ini` file to configure cache settings, whitelist, and time restrictions.
3. Run the `proxy_server.py` script to start the proxy server.
4. Configure your web browser to use the proxy server's IP address and port.

## Disclaimer

This is a simple proxy server implementation for educational purposes. It may not cover all use cases and security considerations required for production environments. Use it responsibly and make necessary security enhancements before deploying it in a production setting.

## Credits

This project was inspired by various proxy server implementations and is intended to demonstrate basic proxy server concepts in Python.
