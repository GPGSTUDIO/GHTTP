def parse(data, safe='1234567890-+_.~qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'):
    value = ''
    for i in data.encode():
        if bytes([i]) in safe.encode():
            value += bytes([i]).decode()
        else:
            value += f'%{bytes([i]).hex().upper()}'
    return value
def unparse(data):
    for i in range(0,256):
        data = data.replace(f'%{bytes([i]).hex()}',chr(i)).replace(f'%{bytes([i]).hex().upper()}',chr(i))
    return data
def parsearg(data,continius=None,encoding='utf-8',safe='1234567890-+_.~qwertyuiopasdfghjklzxcvbnm'):
    if isinstance(continius, dict):
        toret = '?'
        for key, _value in continius.items():
            value = parse(_value)
            toret += f'{key}={value}&'
        return data+toret[:-1] if toret[-1] == '&' else data
    if isinstance(data, str) and continius is None:
        if '?' in data:
            link, args = data.split('?',1)
            args_dict = {}
            for i in args.split('&'):
                key, value = i.split('=',1)
                for i in range(0,256):
                    value = value.replace(f'%{bytes([i]).hex()}',chr(i)).replace(f'%{bytes([i]).hex().upper()}',chr(i))
                value = value.encode('latin-1')
                try: value = value.decode(encoding=encoding)
                except: pass
                if isinstance(value,str):
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace('.', '').isdigit():
                        value = float(value)
                args_dict[key] = value
            return link, args_dict
        else:
            return data, {}