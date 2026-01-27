#!/usr/bin/env python3
"""
Strike7 MCP Server - Minimal Prototype
Implements basic MCP protocol for AI agent integration

Usage:
    python dashboard/mcp_server_minimal.py

Test with Claude Desktop:
    Add to claude_desktop_config.json:
    {
      "mcpServers": {
        "strike7": {
          "command": "python",
          "args": ["/path/to/dashboard/mcp_server_minimal.py"]
        }
      }
    }
"""

import asyncio
import json
import sys
from typing import Any

# Import existing Strike7 components
import os
sys.path.insert(0, os.path.dirname(__file__))

from api.container_manager import ContainerManager
from api.flag_submission import FlagValidator
from api.session_tracker import SessionTracker
import yaml


class Strike7MCPServer:
    """Minimal MCP server for Strike7 benchmarks"""

    def __init__(self):
        """Initialize server with Strike7 components"""
        # Load benchmarks
        benchmarks_file = os.path.join(
            os.path.dirname(__file__),
            'config',
            'benchmarks.yaml'
        )
        with open(benchmarks_file, 'r') as f:
            data = yaml.safe_load(f)
            self.benchmarks = data.get('benchmarks', [])

        # Initialize components
        self.container_manager = ContainerManager(self.benchmarks)
        self.flag_validator = FlagValidator(self.benchmarks)
        self.session_tracker = SessionTracker()

        # Current session
        self.current_session = None

    async def handle_request(self, request: dict) -> dict:
        """Handle incoming MCP request"""
        method = request.get('method')

        if method == 'initialize':
            return await self.handle_initialize(request)
        elif method == 'tools/list':
            return await self.handle_tools_list(request)
        elif method == 'tools/call':
            return await self.handle_tools_call(request)
        elif method == 'resources/list':
            return await self.handle_resources_list(request)
        elif method == 'resources/read':
            return await self.handle_resources_read(request)
        else:
            return {
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'error': {
                    'code': -32601,
                    'message': f'Method not found: {method}'
                }
            }

    async def handle_initialize(self, request: dict) -> dict:
        """Handle initialization request"""
        return {
            'jsonrpc': '2.0',
            'id': request.get('id'),
            'result': {
                'protocolVersion': '0.1.0',
                'capabilities': {
                    'tools': {},
                    'resources': {}
                },
                'serverInfo': {
                    'name': 'strike7-benchmarks',
                    'version': '1.0.0'
                }
            }
        }

    async def handle_tools_list(self, request: dict) -> dict:
        """List available tools"""
        tools = [
            {
                'name': 'strike7_start_benchmark',
                'description': 'Start a Strike7 benchmark container',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'benchmark_id': {
                            'type': 'string',
                            'description': 'Benchmark ID (e.g., S7BEN-EASY-001)'
                        },
                        'timeout_minutes': {
                            'type': 'number',
                            'description': 'Auto-stop timeout in minutes (default: 30)',
                            'default': 30
                        }
                    },
                    'required': ['benchmark_id']
                }
            },
            {
                'name': 'strike7_submit_flag',
                'description': 'Submit a captured flag for validation',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'benchmark_id': {
                            'type': 'string',
                            'description': 'Benchmark ID'
                        },
                        'flag': {
                            'type': 'string',
                            'description': 'Captured flag (format: S7BEN{...})'
                        }
                    },
                    'required': ['benchmark_id', 'flag']
                }
            },
            {
                'name': 'strike7_stop_benchmark',
                'description': 'Stop a running benchmark container',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'benchmark_id': {
                            'type': 'string',
                            'description': 'Benchmark ID'
                        }
                    },
                    'required': ['benchmark_id']
                }
            },
            {
                'name': 'strike7_get_status',
                'description': 'Get status of running containers',
                'inputSchema': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            }
        ]

        return {
            'jsonrpc': '2.0',
            'id': request.get('id'),
            'result': {
                'tools': tools
            }
        }

    async def handle_tools_call(self, request: dict) -> dict:
        """Execute a tool"""
        params = request.get('params', {})
        tool_name = params.get('name')
        arguments = params.get('arguments', {})

        try:
            if tool_name == 'strike7_start_benchmark':
                result = await self.tool_start_benchmark(arguments)
            elif tool_name == 'strike7_submit_flag':
                result = await self.tool_submit_flag(arguments)
            elif tool_name == 'strike7_stop_benchmark':
                result = await self.tool_stop_benchmark(arguments)
            elif tool_name == 'strike7_get_status':
                result = await self.tool_get_status(arguments)
            else:
                return {
                    'jsonrpc': '2.0',
                    'id': request.get('id'),
                    'error': {
                        'code': -32602,
                        'message': f'Unknown tool: {tool_name}'
                    }
                }

            return {
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'result': {
                    'content': [
                        {
                            'type': 'text',
                            'text': json.dumps(result, indent=2)
                        }
                    ]
                }
            }

        except Exception as e:
            return {
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'error': {
                    'code': -32603,
                    'message': f'Tool execution error: {str(e)}'
                }
            }

    async def tool_start_benchmark(self, args: dict) -> dict:
        """Start a benchmark container"""
        benchmark_id = args.get('benchmark_id')
        timeout_minutes = args.get('timeout_minutes', 30)

        result = self.container_manager.start_container(
            benchmark_id,
            force_stop_others=True,
            timeout_minutes=timeout_minutes
        )

        # Mark container start for timing
        if result['status'] == 'success':
            self.flag_validator.mark_container_started(benchmark_id)

        return result

    async def tool_submit_flag(self, args: dict) -> dict:
        """Submit a flag for validation"""
        benchmark_id = args.get('benchmark_id')
        flag = args.get('flag')

        result = self.flag_validator.validate_flag(
            benchmark_id,
            flag,
            session_id=self.current_session
        )

        # Record attempt if session exists
        if self.current_session and result.get('correct') is not None:
            self.session_tracker.record_attempt(
                self.current_session,
                benchmark_id,
                result['correct']
            )

        return result

    async def tool_stop_benchmark(self, args: dict) -> dict:
        """Stop a benchmark container"""
        benchmark_id = args.get('benchmark_id')

        result = self.container_manager.stop_container(benchmark_id)

        # Mark container stopped
        if result['status'] == 'success':
            self.flag_validator.mark_container_stopped(benchmark_id)

        return result

    async def tool_get_status(self, args: dict) -> dict:
        """Get container status"""
        running = self.container_manager.get_running_containers()
        system = self.container_manager.get_system_status()

        return {
            'running_count': len(running),
            'max_allowed': self.container_manager.config['max_concurrent'],
            'containers': running,
            'system': system
        }

    async def handle_resources_list(self, request: dict) -> dict:
        """List available resources"""
        resources = [
            {
                'uri': 'strike7://benchmarks',
                'name': 'Strike7 Benchmarks',
                'description': 'List of all available Strike7 security benchmarks',
                'mimeType': 'application/json'
            },
            {
                'uri': 'strike7://session/progress',
                'name': 'Session Progress',
                'description': 'Current session progress and statistics',
                'mimeType': 'application/json'
            }
        ]

        return {
            'jsonrpc': '2.0',
            'id': request.get('id'),
            'result': {
                'resources': resources
            }
        }

    async def handle_resources_read(self, request: dict) -> dict:
        """Read a resource"""
        params = request.get('params', {})
        uri = params.get('uri')

        try:
            if uri == 'strike7://benchmarks':
                content = json.dumps(self.benchmarks, indent=2)
            elif uri == 'strike7://session/progress':
                if self.current_session:
                    progress = self.session_tracker.get_session_progress(self.current_session)
                    content = json.dumps(progress, indent=2)
                else:
                    content = json.dumps({'error': 'No active session'}, indent=2)
            else:
                return {
                    'jsonrpc': '2.0',
                    'id': request.get('id'),
                    'error': {
                        'code': -32602,
                        'message': f'Unknown resource: {uri}'
                    }
                }

            return {
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'result': {
                    'contents': [
                        {
                            'uri': uri,
                            'mimeType': 'application/json',
                            'text': content
                        }
                    ]
                }
            }

        except Exception as e:
            return {
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'error': {
                    'code': -32603,
                    'message': f'Resource read error: {str(e)}'
                }
            }

    async def run(self):
        """Run the MCP server on stdio"""
        print("Strike7 MCP Server starting...", file=sys.stderr)
        print(f"Loaded {len(self.benchmarks)} benchmarks", file=sys.stderr)

        while True:
            try:
                # Read request from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )

                if not line:
                    break

                request = json.loads(line)
                print(f"Received: {request.get('method')}", file=sys.stderr)

                # Handle request
                response = await self.handle_request(request)

                # Send response to stdout
                print(json.dumps(response), flush=True)

            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}", file=sys.stderr)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)


async def main():
    """Main entry point"""
    server = Strike7MCPServer()
    await server.run()


if __name__ == '__main__':
    asyncio.run(main())
