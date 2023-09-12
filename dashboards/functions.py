def verificar_primer_contacto(lead, prospecto, tiempo_diferencia):
    if tiempo_diferencia >= 60:
        lead.nombre_asesor = None
        prospecto.nombre_asesor = None
        lead.save()
        prospecto.save()
    if lead.tiempo_primer_contacto:
        if lead.tiempo_primer_contacto >= 60:
            lead.nombre_asesor = None
            prospecto.nombre_asesor = None
            lead.save()
            prospecto.save()
