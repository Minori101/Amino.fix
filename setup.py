from setuptools import setup, find_packages

requirements = ["aiohttp", "requests", "asyncio", "typing", "websocket-client==0.57.0", "setuptools", "json_minify", "six"] 

with open("README.md", "r") as stream:
    long_description = stream.read()

setup(
	name="amino.fix",
	license = 'MIT',
	author="Minori",
	version="1.2.18.1",
	author_email="",
	description="Amino 1.2.17 fix lib. Discord - https://discord.gg/Bf3dpBRJHj",
	url="https://github.com/Minori100/Amino.fix",
	packages=find_packages(),
	long_description = long_description,
	install_requires=requirements,
	keywords = [
        'aminoapps',
        'amino.fix',
        'amino',
        'amino-bot',
        'narvii',
        'api',
        'python',
        'python3',
        'python3.x',
        'minori'
    ],
	python_requires='>=3.6',
)