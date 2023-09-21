import re

def verificar_primer_contacto(lead, prospecto, tiempo_diferencia):
    if lead.tiempo_primer_contacto:
        if lead.tiempo_primer_contacto >= 60:
            print("aver esto otro")
            lead.nombre_asesor = None
            prospecto.nombre_asesor = None
            lead.save()
            prospecto.save()
    else:
        if tiempo_diferencia >= 60:
            print("aver esto")
            lead.nombre_asesor = None
            prospecto.nombre_asesor = None
            lead.save()
            prospecto.save()

def separar_nombre(nombre):
    patron = r'(\w)([A-Z])'

    return re.sub(patron, r'\1 \2', nombre)