from core.server import MYTCPServer

tcpserver1=MYTCPServer(('127.0.0.1',8080))
tcpserver1.run()