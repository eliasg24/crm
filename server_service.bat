cd C:\Users\PC\OneDrive\Documentos\crm
call .\myenv\scripts\activate
call daphne -b 201.150.44.27 -p 5015 capnet_apps.asgi:application
