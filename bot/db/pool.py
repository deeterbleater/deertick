import ssl

import asyncpg
import asyncssh

from bot.config import config


async def create_ssh_tunnel():
    conn = await asyncssh.connect(config.get('database', 'host'), username=config.get('database', 'ec2_user'), client_keys=[config.get('database', 'ec2_key')])
    tunnel = await conn.forward_local_port('', 5432, 'localhost', 5432)
    return conn, tunnel


ssl_context = ssl.create_default_context(
    purpose=ssl.Purpose.SERVER_AUTH,
    cafile=config.get('database', 'cert')
)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE  # Only for self-signed certs


async def create_pool():
    ssh_conn, tunnel = await create_ssh_tunnel()
    return await asyncpg.create_pool(
        user=config.get('database', 'user'),
        password=config.get('database', 'password'),
        database=config.get('database', 'database'),
        host=config.get('database', 'host'),
        port=tunnel.get_port(),
        ssl=ssl_context
    )