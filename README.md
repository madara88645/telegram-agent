# Telegram Agent

Telefonundan Telegram ile Windows bilgisayarini kontrol etmen icin basit bir agent.

## Kurulum

PowerShell:

```powershell
[System.Environment]::SetEnvironmentVariable("TELEGRAM_BOT_TOKEN","<TOKEN>","User")
[System.Environment]::SetEnvironmentVariable("TELEGRAM_USER_ID","<USER_ID>","User")
[System.Environment]::SetEnvironmentVariable("TELEGRAM_WORKSPACE","C:\\Users\\User\\Projects","User")
```

```powershell
pip install -r requirements.txt
```

## Calistir

```powershell
python telegram_agent.py
```

Veya:

```powershell
start_telegram.bat
```

## Komutlar

- `/help`
- `/run status`
- `/run tests`
- `/run pip_list`

## Dosya guncelleme (onayli)

Telegram'dan su formatla gonder:

```
edit config.json
<<<
{ ... yeni icerik ... }
>>>
```

Bot diff gosterir ve onay ister. Onaylamadan dosya degistirmez.
