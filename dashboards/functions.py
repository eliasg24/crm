from dashboards.models import Prospecto, Asesor, Catalogo, CatalogoModelo, Lead, CatalogoRespuestasByEtapa, Historial, HistorialVerificaciones, Retomas, VehiculosInteresLead, Evento
from datetime import date, datetime, timedelta
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


def verificar_primer_contacto_todos_los_leads(leads):
    for lead in leads:
        try:
            tiempo_diferencia = int((datetime.now() - lead.fecha_hora_asignacion_asesor.replace(tzinfo=None)).total_seconds() / 60)
            
            prospecto = Prospecto.objects.get(id=lead.prospecto.id)
            if lead.tiempo_primer_contacto or tiempo_diferencia:
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
        except:
            pass


def separar_nombre(nombre):
    patron = r'(\w)([A-Z])'

    return re.sub(patron, r'\1 \2', nombre)