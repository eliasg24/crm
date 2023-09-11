def verificar_primer_contacto(lead, prospecto):
    if lead.tiempo_primer_contacto >= 60:
        lead.nombre_asesor = None
        prospecto.nombre_asesor = None
        lead.save()
        prospecto.save()