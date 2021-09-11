### Discord
`https://discord.gg/Bf3dpBRJHj`
### About lib
`Fix Amino.py 1.2.17`
### How to install?
`pip install amino.fix`

### Example
`import asyncio`
`import aminofix`

`async def main():`
    `client = aminofix.Client()`
    `client.web_login(email='email',password='password')`
    `sub_client = aminofix.SubClient(comId='comId', profile=client.profile)`
`if __name__ == '__main__':`
    `asyncio.get_event_loop().run_until_complete(main())`
