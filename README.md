# eskiz-sms

eskiz-sms package for eskiz.uz/sms

Discussion group: https://t.me/+xFkMROBeFp45ZmQ0

[![Downloads](https://pepy.tech/badge/eskiz-sms)](https://pepy.tech/project/eskiz-sms)
[![Downloads](https://pepy.tech/badge/eskiz-sms/month)](https://pepy.tech/project/eskiz-sms)
[![Downloads](https://pepy.tech/badge/eskiz-sms/week)](https://pepy.tech/project/eskiz-sms)

> :warning: **Please use the latest version. In previous versions, there are a lot of mistakes, bugs**

# Installation

```
pip install eskiz_sms
```

# Quickstart

```python
from eskiz_sms import EskizSMS

email = "your_email@mail.com"
password = "your_password"
eskiz = EskizSMS(email=email, password=password)
eskiz.send_sms('998991234567', 'message', from_whom='4546', callback_url=None)
```

### Using pre-saved token

```python
from eskiz_sms import EskizSMS

your_saved_token = 'eySomething9320'
eskiz = EskizSMS('email', 'password')
eskiz.token.set(your_saved_token)

eskiz.send_sms('998901234567', message='message')
```

### Saving token to env file

If you set `save_token=True` it will save the token to env file

```python
from eskiz_sms import EskizSMS

eskiz = EskizSMS('email', 'password', save_token=True, env_file_path='.env')
# Don't forget to add env file to .gitignore!
response = eskiz.send_sms('998901234567', message='message')
```
### Async usage

```python
import asyncio

from eskiz_sms.async_ import EskizSMS


async def main():
    eskiz = EskizSMS('email', 'password')
    response = await eskiz.send_sms('998901234567', 'Hello, World!')


asyncio.run(main())
```

