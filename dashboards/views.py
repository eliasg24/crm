# Django
import re
from django.db.models import Q, Max, Subquery, Count
from django.db.models.functions import Coalesce
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.http.response import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, ListView, TemplateView, DetailView, DeleteView, UpdateView
from django.views.generic.base import View

# Functions
from dashboards import functions
from crm import settings

# Forms
from dashboards.forms import LeadForm

# Models
from django.contrib.auth.models import User, Group
from dashboards.models import Prospecto, Asesor, Catalogo, CatalogoModelo, Lead, CatalogoRespuestasByEtapa, Historial, HistorialVerificaciones, Retomas, VehiculosInteresLead, Evento

# Utilities
from datetime import date, datetime, timedelta
import json
from openpyxl import load_workbook

class LoginView(auth_views.LoginView):
    # Vista de Login

    template_name = "Login.html"
    redirect_authenticated_user = True


class LogoutView(LoginRequiredMixin, auth_views.LogoutView):
    # Vista de Logout
    pass

class CapturaView(LoginRequiredMixin, TemplateView):
    # Vista de Captura

    template_name = "Captura.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(username=self.request.user)
        try:
            asesor_actual = Asesor.objects.get(nombre=functions.separar_nombre(user.username))
        except:
            asesor_actual = {}
            asesor_actual["pk"] = 0

        calendario_general = True
        origenes_lead = Catalogo.objects.filter(clasificacion="Origen Lead")
        for grupo in self.request.user.groups.all():
            if grupo.name == "Asesor":
                calendario_general = False
                origenes_lead = Catalogo.objects.filter(clasificacion="Origen Lead Asesor")

        asesores = Asesor.objects.all()
        grupo = Group.objects.get(name="Asesor")

        marcas = CatalogoModelo.objects.all().values("marca").distinct()

        now = datetime.now()

        cantidad_morato = Lead.objects.filter(sala="Morato", fecha_apertura__month=now.month).count()
        cantidad_127 = Lead.objects.filter(sala="127", fecha_apertura__month=now.month).count()

        today = datetime.now()


        context["asesor_actual"] = asesor_actual
        context["calendario_general"] = calendario_general
        context["cantidad_morato"] = cantidad_morato
        context["cantidad_127"] = cantidad_127
        context["marcas"] = marcas
        context["today"] = today
        context["origenes_lead"] = origenes_lead
        context["user"] = user
        return context

    def post(self, request):
        r = request.POST
        user = User.objects.get(username=self.request.user)
        
        print(r)
        if r.get("celular_verificar", None):
            prospecto = Prospecto.objects.get(celular=r.get("celular_verificar", None))
            print(prospecto)
            if prospecto:
                ultimo_lead = Lead.objects.filter(prospecto=prospecto).last()
                ultimo_lead = {"nombre_anfitrion": ultimo_lead.nombre_anfitrion, "fecha_apertura": ultimo_lead.fecha_apertura.date(), "respuesta": ultimo_lead.respuesta, "estado": ultimo_lead.estado, "nombre_asesor": ultimo_lead.nombre_asesor,}
                alerta = {"alerta_celular": True, "ultimo_lead": ultimo_lead}
            else:
                alerta = {"alerta_celular": False}

            return JsonResponse(alerta, safe=False)
        
        if r.get("marca", None):
            marca = r.get("marca", None)
            modelos = CatalogoModelo.objects.filter(marca=marca.title())
            print(marca.title())
            print("modelos")
            print(modelos)
            modelos = list(modelos.values())

            print(modelos)

            return JsonResponse(modelos, safe=False)
        if r.get("NombreProspecto", None):
            nombre = r.get("NombreProspecto", None)
            apellido_paterno = r.get("ApellidoPProspecto", None)
            apellido_materno = r.get("ApellidoMProspecto", None)
            celular = r.get("Celular", None)
            correo = r.get("Correo", None)
            origen_lead = r.get("OrigenLead", None)
            campania = r.get("Campania", None)
            tipo_documento = r.get("TipoDocumento", None)
            documento = r.get("Documento", None)
            politica_privacidad = r.get("PoliticaPrivacidad", None)
            if not politica_privacidad:
                politica_privacidad = False
            else:
                politica_privacidad = True
            anfitrion = r.get("Anfitrion", None)
            sala = r.get("Sala", None)
            nombre_asesor = r.get("Asesor", None)
            marcas_interes = r.getlist("MarcasInteres", None)
            modelo = r.getlist("Modelo", None)
            color = r.getlist("Color", None)
            marca_comentario = r.getlist("MarcaComentario", None)
            print(marcas_interes)
            print(modelo)
            print(color)
            print(marca_comentario)
            m_lista = []
            for m in range(len(modelo)):
                m_lista.append({"marca": marcas_interes[m],
                     "modelo": modelo[m],
                     "color": color[m],
                     "marca_comentario": marca_comentario[m],
                     "codigo": None,
                     "precio": None
                    })
            
            marcas = {"marcas": m_lista}
            comentario = r.get("Comentario", None)
            test_drive = r.get("TestDrive", None)
            if not test_drive:
                test_drive = False
            else:
                test_drive = True
            prospecto = Prospecto.objects.create(nombre=nombre,
                                apellido_paterno=apellido_paterno,
                                apellido_materno=apellido_materno,
                                celular=celular,
                                correo=correo,
                                fecha_captura=datetime.now(),
                                nombre_asesor=nombre_asesor,
                                anfitrion=anfitrion,
                                fecha_hora_asignacion_asesor=datetime.now(),
                                politica_privacidad=politica_privacidad,
                                )
            
            lead = Lead.objects.create(prospecto=prospecto,
                                origen_lead=origen_lead,
                                marcas_interes=marcas,
                                sala=sala,
                                etapa="No contactado",
                                respuesta="Sin contactar",
                                estado="No contactado",
                                status="Frío",
                                interes="Venta",
                                activo=True,
                                fecha_apertura=datetime.now(),
                                comentario=comentario,
                                campania=campania,
                                tipo_documento=tipo_documento,
                                documento=documento,
                                test_drive=test_drive,
                                nombre_asesor=nombre_asesor,
                                fecha_hora_asignacion_asesor=datetime.now(),
                                nombre_anfitrion=anfitrion,
                                )
            Historial.objects.create(lead=lead,
                        fecha=datetime.now(),
                        responsable=user,
                        operacion=f"Creación Lead",
                        comentarios=comentario
                        )
            VehiculosInteresLead.objects.create(lead=lead,
                                            marca=marcas_interes[0],
                                            modelo=modelo[0],
                                            color=color[0],
                                            comentario=marca_comentario[0],
                                            peritaje=False,
                                            cotizar=False,
                                            aprobacion=False,
                                            precio=False,
                                            separado=False,
                                            facturado=False,
                                            mostrado=True
                                            )
            return HttpResponseRedirect(reverse_lazy('dashboards:captura'))



        if r.get("sala", None):
            sala = r.get("sala", None)
            asesores = Asesor.objects.filter(sala=sala)
            print("asesores")
            print(asesores)
            asesores = list(asesores.values())

            return JsonResponse(asesores, safe=False)

        if r.get("etapa", None):
            etapa = r.get("etapa", None)
            respuestas = CatalogoRespuestasByEtapa.objects.filter(etapa=etapa).values("respuesta").distinct()
            print("respuestas")
            print(respuestas)
            respuestas = list(respuestas)

            return JsonResponse(respuestas, safe=False)

        

class CapturaReasignamientoView(LoginRequiredMixin, DetailView):
    # Vista de Captura Reasignamiento

    template_name = "CapturaReasignamiento.html"
    slug_field = "lead"
    slug_url_kwarg = "lead"
    queryset = Lead.objects.all()
    context_object_name = "lead"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lead = self.get_object()
        user = User.objects.get(username=self.request.user)
        try:
            asesor_actual = Asesor.objects.get(nombre=functions.separar_nombre(user.username))
        except:
            asesor_actual = {}
            asesor_actual["pk"] = 0

        calendario_general = True
        for grupo in self.request.user.groups.all():
            if grupo.name == "Asesor":
                calendario_general = False

        asesores = Asesor.objects.all()
        grupo = Group.objects.get(name="Asesor")

        marcas = CatalogoModelo.objects.all().values("marca").distinct()

        now = datetime.now()

        cantidad_morato = Lead.objects.filter(sala="Morato", fecha_apertura__month=now.month).count()
        cantidad_127 = Lead.objects.filter(sala="127", fecha_apertura__month=now.month).count()

        today = datetime.now()

        context["asesor_actual"] = asesor_actual
        context["calendario_general"] = calendario_general
        context["cantidad_morato"] = cantidad_morato
        context["cantidad_127"] = cantidad_127
        context["marcas"] = marcas
        context["today"] = today
        context["user"] = user
        return context
    
    def post(self, request, pk):
        r = request.POST
        user = User.objects.get(username=self.request.user)
        
        print(r)
        

        if r.get("sala", None):
            sala = r.get("sala", None)
            asesores = Asesor.objects.filter(sala=sala)
            print("asesores")
            print(asesores)
            asesores = list(asesores.values())

            return JsonResponse(asesores, safe=False)

        if r.get("Asesor", None):
            sala = r.get("Sala", None)
            nombre_asesor = r.get("Asesor", None)

            lead = Lead.objects.get(pk=pk)
            lead.sala = sala
            lead.nombre_asesor = nombre_asesor
            lead.fecha_hora_asignacion_asesor = datetime.now()
            lead.fecha_hora_reasignacion = datetime.now()
            lead.tiempo_primer_contacto = None
            lead.fecha_primer_contacto = None
            lead.etapa = "No contactado"
            lead.respuesta = "Sin contactar"
            lead.estado = "No contactado"
            lead.save()
            
            print(lead)
            print(sala)
            print(nombre_asesor)

            Historial.objects.create(lead=lead,
                        fecha=datetime.now(),
                        responsable=user,
                        operacion=f"Reasignación de asesor a {nombre_asesor}",
                        comentarios=None
                        )
            return HttpResponseRedirect(reverse_lazy('dashboards:captura'))


class DetalleClienteView(LoginRequiredMixin, TemplateView):
    # Vista de Detalle Cliente

    template_name = "DetalleCliente.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(username=self.request.user)
        try:
            asesor_actual = Asesor.objects.get(nombre=functions.separar_nombre(user.username))
        except:
            asesor_actual = {}
            asesor_actual["pk"] = 0
        print(user)

        calendario_general = True
        for grupo in self.request.user.groups.all():
            if grupo.name == "Asesor":
                calendario_general = False

        context["asesor_actual"] = asesor_actual
        context["calendario_general"] = calendario_general
        context["user"] = user

        return context

class DetalleClienteNuevoView(LoginRequiredMixin, DetailView):
    # Vista de Detalle Cliente Nuevo

    template_name = "DetalleClienteNuevo.html"
    slug_field = "lead"
    slug_url_kwarg = "lead"
    queryset = Lead.objects.all()
    context_object_name = "lead"
    form_class = LeadForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lead = self.get_object()

        user = User.objects.get(username=self.request.user)
        try:
            asesor_actual = Asesor.objects.get(nombre=functions.separar_nombre(user.username))
        except:
            asesor_actual = {}
            asesor_actual["pk"] = 0

        historial = Historial.objects.filter(lead=lead)

        prospecto = Prospecto.objects.get(pk=lead.prospecto.pk)
        try:
            sala = Asesor.objects.get(nombre=lead.nombre_asesor).sala
        except:
            sala = None
        asesores = Asesor.objects.filter(sala=sala)

        dias_totales = (datetime.now() - lead.fecha_hora_asignacion_asesor.replace(tzinfo=None)).days

        tiempo_diferencia = int((datetime.now() - lead.fecha_hora_asignacion_asesor.replace(tzinfo=None)).total_seconds() / 60)
        
        print(datetime.now())
        print(lead.fecha_hora_asignacion_asesor.replace(tzinfo=None))
        print((datetime.now() - lead.fecha_hora_asignacion_asesor.replace(tzinfo=None)).total_seconds())
        print(tiempo_diferencia)
        print(lead.tiempo_primer_contacto)

        if lead.tiempo_primer_contacto or tiempo_diferencia:
            functions.verificar_primer_contacto(lead, prospecto, tiempo_diferencia)
        
        marcas_interes = eval(lead.marcas_interes)
        marcas = CatalogoModelo.objects.all().values("marca").distinct()
        etapas = CatalogoRespuestasByEtapa.objects.values("etapa").distinct()
        respuestas = CatalogoRespuestasByEtapa.objects.filter(etapa=lead.etapa).values("respuesta").distinct()

        mostrar_evento = False
        calendario_general = True
        for grupo in self.request.user.groups.all():
            if grupo.name == "Asesor":
                mostrar_evento = True
                calendario_general = False
            if grupo.name == "Admin":
                mostrar_evento = True

        context["asesor_actual"] = asesor_actual
        context["asesores"] = asesores
        context["calendario_general"] = calendario_general
        context["dias_totales"] = dias_totales
        context["etapas"] = etapas
        context["historial"] = historial
        context["marcas"] = marcas
        context["marcas_interes"] = marcas_interes
        context["mostrar_evento"] = mostrar_evento
        context["prospecto"] = prospecto
        context["respuestas"] = respuestas
        context["sala"] = sala
        context["tiempo_diferencia"] = tiempo_diferencia
        context["user"] = user

        return context
    
    def post(self, request, pk):

        lead = Lead.objects.get(pk=pk)
        prospecto = Prospecto.objects.get(pk=lead.prospecto.pk)
        user = User.objects.get(username=self.request.user)
        if request.POST.get("Lead_Etapa"):
            lista_historial = []
            if lead.etapa != request.POST.get("Lead_Etapa"):
                lista_historial.append(f"Etapa. (Antes: {lead.etapa}. Ahora: {request.POST.get('Lead_Etapa')})")
            lead.etapa = request.POST.get("Lead_Etapa")
            lead.estado = request.POST.get("Lead_Etapa")
            if lead.respuesta != request.POST.get("Lead_Respuesta"):
                lista_historial.append(f"Respuesta. (Antes: {lead.respuesta}. Ahora: {request.POST.get('Lead_Respuesta')})")
            lead.respuesta = request.POST.get("Lead_Respuesta")
            comentario = request.POST.get("Lead_Comentario")
            if lead.comentario != comentario and comentario != "None":
                lista_historial.append(f"Comentario. (Antes: {lead.comentario}. Ahora: {request.POST.get('Lead_Comentario')})")
            lead.comentario = request.POST.get("Lead_Comentario")
            if request.POST.get("Lead_Respuesta") != "Sin contactar":
                if not(lead.fecha_primer_contacto):
                    lead.fecha_primer_contacto = datetime.now()
                    tiempo_primer_contacto = datetime.now() - lead.fecha_hora_asignacion_asesor.replace(tzinfo=None)
                    lead.tiempo_primer_contacto = tiempo_primer_contacto.total_seconds() / 60
            
            marcas_interes = request.POST.getlist("MarcasInteres[]", None)
            modelo = json.loads(request.POST.get("Modelo", None))
            color = json.loads(request.POST.get("Color", None))
            codigo = json.loads(request.POST.get("Codigo", None))
            precio = json.loads(request.POST.get("Precio", None))
            
            codigo_vehiculo = request.POST.getlist("CodigoVehiculo", None)
            precio_vehiculo = request.POST.getlist("PrecioVehiculo", None)

            m_lista = eval(lead.marcas_interes)["marcas"]
            print("aver")
            print(request.POST)
            print("marcas_interes")
            print(marcas_interes)
            print("modelo")
            print(modelo)
            print("color")
            print(color)
            
            for ma in range(len(marcas_interes)):
                for mo in range(len(modelo[ma])):
                    m_lista.append({"marca": marcas_interes[ma],
                        "modelo": modelo[ma][mo],
                        "color": color[ma][mo],
                        "marca_comentario": None,
                        "codigo": codigo[ma][mo],
                        "precio": precio[ma][mo]
                        })
            
            marcas = {"marcas": m_lista}

            print(lead.marcas_interes)
            print(marcas)

            if str(lead.marcas_interes) != str(marcas):
                lista_historial.append(f"Marcas Interes. (Se agregaron: {m_lista})")
            lead.marcas_interes = marcas
            lead.save()
            
            if lista_historial:
                Historial.objects.create(lead=lead,
                                        fecha=datetime.now(),
                                        responsable=user,
                                        operacion=f"Se modificaron los siguientes campos: {lista_historial}",
                                        comentarios=comentario
                                        )
            return redirect("dashboards:detallenuevo", pk)
        elif request.POST.get("ProspectoNombre"):
            lista_historial = []
            if prospecto.nombre != request.POST.get("ProspectoNombre"):
                lista_historial.append("Nombre")
            prospecto.nombre = request.POST.get("ProspectoNombre")
            if prospecto.apellido_paterno != request.POST.get("ProspectoApPaterno"):
                lista_historial.append("Apellido Paterno")
            prospecto.apellido_paterno = request.POST.get("ProspectoApPaterno")
            if prospecto.apellido_materno != request.POST.get("ProspectoApMaterno"):
                lista_historial.append("Apellido Materno")
            prospecto.apellido_materno = request.POST.get("ProspectoApMaterno")
            if prospecto.celular != request.POST.get("ProspectoCelular"):
                lista_historial.append("Celular")
            prospecto.celular = request.POST.get("ProspectoCelular")
            if prospecto.correo != request.POST.get("ProspectoCorreo"):
                lista_historial.append("Correo")
            prospecto.correo = request.POST.get("ProspectoCorreo")
            prospecto.anfitrion = request.POST.get("Lead_NombreAnfitrion")
            prospecto.nombre_asesor = request.POST.get("ProspectoAsesor")
            if prospecto.contacto_nombre != request.POST.get("NombreContacto"):
                lista_historial.append("Nombre Contacto")
            prospecto.contacto_nombre = request.POST.get("NombreContacto")
            if prospecto.contacto_telefono != request.POST.get("CelularContacto"):
                lista_historial.append("Celular Contacto")
            prospecto.contacto_telefono = request.POST.get("CelularContacto")
            if request.POST.get("PoliticaDatos") == "true":
                politica_privacidad = True
            else:
                politica_privacidad = False
            if prospecto.politica_privacidad != politica_privacidad:
                lista_historial.append("Politica Datos")
            prospecto.politica_privacidad = politica_privacidad
            prospecto.save()

            if lead.nombre_anfitrion != request.POST.get("Lead_NombreAnfitrion"):
                lista_historial.append("Anfitrión")
            lead.nombre_anfitrion = request.POST.get("Lead_NombreAnfitrion")
            if lead.campania != request.POST.get("LeadCampania"):
                lista_historial.append("Campaña")
            lead.campania = request.POST.get("LeadCampania")
            if lead.tipo_documento != request.POST.get("LeadTipoDocumento"):
                lista_historial.append("Tipo de documento")
            lead.tipo_documento = request.POST.get("LeadTipoDocumento")
            if lead.documento != request.POST.get("LeadDocumento"):
                lista_historial.append("Documento")
            lead.documento = request.POST.get("LeadDocumento")
            if request.POST.get("TestDrive") == "true":
                test_drive = True
            else:
                test_drive = False
            if lead.test_drive != test_drive:
                lista_historial.append("TestDrive")
            lead.test_drive = test_drive
            lead.save()
            if lista_historial:
                Historial.objects.create(lead=lead,
                                        fecha=datetime.now(),
                                        responsable=user,
                                        operacion=f"Se modificaron los siguientes campos: {lista_historial}"
                                        )
            return JsonResponse(prospecto.pk, safe=False)
        elif request.POST.get("EstadoLlamada"):
            lista_historial = []

            estado_llamada = request.POST.get("EstadoLlamada")
            tipo_solicitud = request.POST.get("TipoSolicitud")
            reasignado = request.POST.get("AsesorReasignado")
            observaciones = request.POST.get("Observaciones")
            
            if reasignado:
                lead.nombre_asesor = reasignado
                lead.fecha_hora_reasignacion = datetime.now()
            lead.estado_llamada_verificacion = estado_llamada
            lead.tipo_solicitud_verificacion = tipo_solicitud
            lead.save()

            HistorialVerificaciones.objects.create(lead=lead,
                                                   estado_llamada=estado_llamada,
                                                   tipo_solicitud=tipo_solicitud,
                                                   responsable=user,
                                                   reasignado=reasignado,
                                                   observaciones=observaciones,
                                                   fecha_hora_verificacion=datetime.now(),
                                                   tipo="venta"
                                                   )
            if not(reasignado):
                reasignado = ""
            else:
                reasignado = f"Reasignado a: {reasignado}"


            Historial.objects.create(lead=lead,
                                    fecha=datetime.now(),
                                    responsable=user,
                                    operacion=f"Se hizo la verificación. Estado de llamada: {estado_llamada}. Tipo de solicitud: {tipo_solicitud}. {reasignado}",
                                    comentarios=observaciones
                                    )
            return JsonResponse(prospecto.pk, safe=False)
        elif request.POST.get("modelo_retoma"):
            lista_historial = []

            modelo_retoma = request.POST.get("modelo_retoma")
            valor_retoma = request.POST.get("valor_retoma")
            total_retoma = request.POST.get("total_retoma")
            total_restante = request.POST.get("total_restante")
            
            Retomas.objects.create(lead=lead,
                                        modelo=modelo_retoma,
                                        valor=valor_retoma,
                                        total=total_retoma,
                                        total_restante=total_restante,
                                        )

            Historial.objects.create(lead=lead,
                                    fecha=datetime.now(),
                                    responsable=user,
                                    operacion=f"Se hizo la retoma. Modelo: {modelo_retoma}. Valor: {valor_retoma}. Total: {total_retoma}. Total restante: {total_restante}.",
                                    )
            return JsonResponse(prospecto.pk, safe=False)
        elif request.POST.get("accion"):
            lista_historial = []

            accion = request.POST.get("accion")
            vehiculo_acciones = request.POST.get("vehiculo_acciones")
            if accion == "Separar":
                nombre_accion = "Separado"
                separado = True
                facturado = False
                mostrado = False
            elif accion == "Facturar":
                nombre_accion = "Facturado"
                separado = False
                facturado = True
                mostrado = False
            elif accion == "Mostrar":
                nombre_accion = "Mostrado en tabla"
                separado = False
                facturado = False
                mostrado = True

            marcas_interes = eval(lead.marcas_interes)

            vehiculo_acciones = vehiculo_acciones.split("/")

            if separado == True or facturado == True:
                VehiculosInteresLead.objects.filter(lead=lead, mostrado=False).delete()

            if mostrado == True:
                VehiculosInteresLead.objects.filter(lead=lead, mostrado=True).delete()
            
            VehiculosInteresLead.objects.create(lead=lead,
                                                marca=vehiculo_acciones[0],
                                                modelo=vehiculo_acciones[1],
                                                color=vehiculo_acciones[2],
                                                codigo_vehiculo=vehiculo_acciones[3],
                                                peritaje=False,
                                                cotizar=False,
                                                aprobacion=False,
                                                precio=False,
                                                separado=separado,
                                                facturado=facturado,
                                                mostrado=mostrado
                                        )

            Historial.objects.create(lead=lead,
                                    fecha=datetime.now(),
                                    responsable=user,
                                    operacion=f"Se hizo el {nombre_accion}. Marca: {vehiculo_acciones[0]}. Modelo: {vehiculo_acciones[1]}.",
                                    )
            return JsonResponse(prospecto.pk, safe=False)
        elif request.POST.get("EventoNombre"):

            nombre = request.POST.get("EventoNombre")
            tipo = request.POST.get("EventoTipo")
            telefono_cliente = request.POST.get("EventoTelefono")
            observaciones = request.POST.get("EventoObservaciones")
            asesor = request.POST.get("EventoAsesor")
            fecha_hora = request.POST.get("EventoFechaHora")
            tiempo_evento = request.POST.get("EventoTiempo")

            print("fecha_hora")
            print(fecha_hora)
            print(type(fecha_hora))

            print(datetime.strptime(fecha_hora,"%Y-%m-%dT%H:%M"))

            print(type(datetime.strptime(fecha_hora,"%Y-%m-%dT%H:%M")))
            
            evento = Evento.objects.create(nombre=nombre,
                                           tipo=tipo,
                                           telefono_cliente=telefono_cliente,
                                           observaciones=observaciones,
                                           asesor=Asesor.objects.get(nombre=asesor),
                                           fecha_hora=datetime.strptime(fecha_hora,"%Y-%m-%dT%H:%M"),
                                           lead=lead,
                                           tiempo_evento=tiempo_evento
                                           )
            Historial.objects.create(lead=lead,
                                    fecha=datetime.now(),
                                    responsable=user,
                                    operacion=f"Se creó un evento. Nombre: {nombre}. Tipo: {tipo}. Observaciones: {observaciones}",
                                    )
            return JsonResponse(evento.pk, safe=False)
    
        if request.POST.get("select_accion"):
            accion = request.POST.get("select_accion")
            try:
                if accion == "Separar":
                    vehiculo = VehiculosInteresLead.objects.get(lead=lead, separado=True)
                elif accion == "Facturar":
                    vehiculo = VehiculosInteresLead.objects.get(lead=lead, facturado=True)
                elif accion == "Mostrar":
                    vehiculo = VehiculosInteresLead.objects.get(lead=lead, mostrado=True)
                print("vehiculo")
                print(vehiculo)
                vehiculo = f"{vehiculo.marca} {vehiculo.modelo}"
                return JsonResponse(vehiculo, safe=False)
            except:
                return JsonResponse(None, safe=False)

class OperativoAnfitrionView(LoginRequiredMixin, TemplateView):
    # Vista de Operativo Anfitrion

    template_name = "OperativoAnfitrion.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(username=self.request.user)
        
        leads = Lead.objects.filter(activo=True, nombre_asesor__isnull=False).order_by("-id")

        functions.verificar_primer_contacto_todos_los_leads(leads)
        
        try:
            asesor_actual = Asesor.objects.get(nombre=functions.separar_nombre(user.username))
        except:
            asesor_actual = {}
            asesor_actual["pk"] = 0
        print(user)

        calendario_general = True
        for grupo in self.request.user.groups.all():
            if grupo.name == "Asesor":
                calendario_general = False

        leads_agendados = Lead.objects.filter(nombre_asesor__isnull=False, activo=True).exclude(etapa="Desistido").order_by("-id")
        leads_primer_contacto = Lead.objects.filter(nombre_asesor__isnull=True, activo=True).order_by("-id")

        verificaciones = HistorialVerificaciones.objects.select_related("lead").order_by("-id")

        mostrado_marcas = VehiculosInteresLead.objects.filter(mostrado=True).values("lead").distinct().values("lead", "marca", "modelo")

        print(verificaciones)

        anfitriones_agendados = leads_agendados.values("nombre_anfitrion")
        tipos_solicitud_agendados = leads_agendados.values("tipo_solicitud_verificacion")
        asesores_agendados = leads_agendados.values("nombre_asesor")
        salas_agendados = leads_agendados.values("sala")

        context["anfitriones_agendados"] = anfitriones_agendados
        context["asesores_agendados"] = asesores_agendados
        context["asesor_actual"] = asesor_actual
        context["calendario_general"] = calendario_general
        context["cantidad_agendados"] = leads_agendados.count()
        context["cantidad_verificados"] = verificaciones.count()
        context["cantidad_primer_contacto"] = leads_primer_contacto.count()
        context["leads_agendados"] = leads_agendados
        context["leads_primer_contacto"] = leads_primer_contacto
        context["mostrado_marcas"] = mostrado_marcas
        context["salas_agendados"] = salas_agendados
        context["tipos_solicitud_agendados"] = tipos_solicitud_agendados
        context["user"] = user
        context["verificaciones"] = verificaciones

        return context
    
class OperativoAsesorView(LoginRequiredMixin, TemplateView):
    # Vista de Operativo Asesor

    template_name = "OperativoAsesor.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(username=self.request.user)
        try:
            asesor_actual = Asesor.objects.get(nombre=functions.separar_nombre(user.username))
        except:
            asesor_actual = {}
            asesor_actual["pk"] = 0
        print(user)
        
        calendario_general = True
        for grupo in self.request.user.groups.all():
            if grupo.name == "Asesor":
                calendario_general = False

        leads = Lead.objects.filter(activo=True, nombre_asesor__isnull=False).order_by("-id")

        functions.verificar_primer_contacto_todos_los_leads(leads)

        if calendario_general == False:
            leads_no_contactado = Lead.objects.filter(etapa="No contactado", activo=True, nombre_asesor=user.username).order_by("-id")
            leads_interaccion = Lead.objects.filter(etapa="Interaccion", activo=True, nombre_asesor=user.username).order_by("-id")
            leads_oportunidad = Lead.objects.filter(etapa="Oportunidad", activo=True, nombre_asesor=user.username).order_by("-id")
            leads_pedido = Lead.objects.filter(etapa="Pedido", activo=True, nombre_asesor=user.username).order_by("-id")
        else:

            leads_no_contactado = Lead.objects.filter(etapa="No contactado", activo=True, nombre_asesor__isnull=False).order_by("-id")
            leads_interaccion = Lead.objects.filter(etapa="Interaccion", activo=True, nombre_asesor__isnull=False).order_by("-id")
            leads_oportunidad = Lead.objects.filter(etapa="Oportunidad", activo=True, nombre_asesor__isnull=False).order_by("-id")
            leads_pedido = Lead.objects.filter(etapa="Pedido", activo=True, nombre_asesor__isnull=False).order_by("-id")
        respuestas = CatalogoRespuestasByEtapa.objects.all()
        estados = CatalogoRespuestasByEtapa.objects.all()

        mostrado_marcas = VehiculosInteresLead.objects.filter(mostrado=True).values("lead", "mostrado").distinct().annotate(latest=Max("id")).values("lead", "marca", "modelo")

        origenes_lead_no_contactado = leads_no_contactado.values("origen_lead")
        origenes_lead_interaccion = leads_interaccion.values("origen_lead")
        origenes_lead_oportunidad = leads_oportunidad.values("origen_lead")
        origenes_lead_pedido = leads_pedido.values("origen_lead")

        respuestas_no_contactado = leads_no_contactado.values("respuesta")
        respuestas_interaccion = leads_interaccion.values("respuesta")
        respuestas_oportunidad = leads_oportunidad.values("respuesta")
        respuestas_pedido = leads_pedido.values("respuesta")

        estados_no_contactado = leads_no_contactado.values("estado")
        estados_interaccion = leads_interaccion.values("estado")
        estados_oportunidad = leads_oportunidad.values("estado")
        estados_pedido = leads_pedido.values("estado")

        asesores_no_contactado = leads_no_contactado.values("nombre_asesor")
        asesores_interaccion = leads_interaccion.values("nombre_asesor")
        asesores_oportunidad = leads_oportunidad.values("nombre_asesor")
        asesores_pedido = leads_pedido.values("nombre_asesor")

        salas_no_contactado = leads_no_contactado.values("sala")
        salas_interaccion = leads_interaccion.values("sala")
        salas_oportunidad = leads_oportunidad.values("sala")
        salas_pedido = leads_pedido.values("sala")

        mostrado_marcas_no_contactado = VehiculosInteresLead.objects.filter(mostrado=True).filter(lead__in=leads_no_contactado).values("lead", "mostrado").distinct().annotate(latest=Max("id")).values("lead", "marca", "modelo")
        mostrado_marcas_interaccion = VehiculosInteresLead.objects.filter(mostrado=True).filter(lead__in=leads_interaccion).values("lead", "mostrado").distinct().annotate(latest=Max("id")).values("lead", "marca", "modelo")
        mostrado_marcas_oportunidad = VehiculosInteresLead.objects.filter(mostrado=True).filter(lead__in=leads_oportunidad).values("lead", "mostrado").distinct().annotate(latest=Max("id")).values("lead", "marca", "modelo")
        mostrado_marcas_pedido = VehiculosInteresLead.objects.filter(mostrado=True).filter(lead__in=leads_pedido).values("lead", "mostrado").distinct().annotate(latest=Max("id")).values("lead", "marca", "modelo")

        context["asesor_actual"] = asesor_actual
        context["asesores_no_contactado"] = asesores_no_contactado
        context["asesores_interaccion"] = asesores_interaccion
        context["asesores_oportunidad"] = asesores_oportunidad
        context["asesores_pedido"] = asesores_pedido
        context["calendario_general"] = calendario_general
        context["cantidad_no_contactado"] = leads_no_contactado.count()
        context["cantidad_interaccion"] = leads_interaccion.count()
        context["cantidad_oportunidad"] = leads_oportunidad.count()
        context["cantidad_pedido"] = leads_pedido.count()
        context["estados"] = estados
        context["estados_no_contactado"] = estados_no_contactado
        context["estados_interaccion"] = estados_interaccion
        context["estados_oportunidad"] = estados_oportunidad
        context["estados_pedido"] = estados_pedido
        context["leads_no_contactado"] = leads_no_contactado
        context["leads_interaccion"] = leads_interaccion
        context["leads_oportunidad"] = leads_oportunidad
        context["leads_pedido"] = leads_pedido
        context["mostrado_marcas"] = mostrado_marcas
        context["mostrado_marcas_no_contactado"] = mostrado_marcas_no_contactado
        context["mostrado_marcas_interaccion"] = mostrado_marcas_interaccion
        context["mostrado_marcas_oportunidad"] = mostrado_marcas_oportunidad
        context["mostrado_marcas_pedido"] = mostrado_marcas_pedido
        context["origenes_lead_no_contactado"] = origenes_lead_no_contactado
        context["origenes_lead_interaccion"] = origenes_lead_interaccion
        context["origenes_lead_oportunidad"] = origenes_lead_oportunidad
        context["origenes_lead_pedido"] = origenes_lead_pedido
        context["respuestas"] = respuestas
        context["respuestas_no_contactado"] = respuestas_no_contactado
        context["respuestas_interaccion"] = respuestas_interaccion
        context["respuestas_oportunidad"] = respuestas_oportunidad
        context["respuestas_pedido"] = respuestas_pedido
        context["salas_no_contactado"] = salas_no_contactado
        context["salas_interaccion"] = salas_interaccion
        context["salas_oportunidad"] = salas_oportunidad
        context["salas_pedido"] = salas_pedido
        context["user"] = user

        return context
    
class ReportesView(LoginRequiredMixin, TemplateView):
    # Vista de Reportes

    template_name = "Reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(username=self.request.user)

        leads = Lead.objects.filter(activo=True, nombre_asesor__isnull=False).order_by("-id")

        functions.verificar_primer_contacto_todos_los_leads(leads)

        try:
            asesor_actual = Asesor.objects.get(nombre=functions.separar_nombre(user.username))
        except:
            asesor_actual = {}
            asesor_actual["pk"] = 0
        print(user)

        calendario_general = True
        for grupo in self.request.user.groups.all():
            if grupo.name == "Asesor":
                calendario_general = False

        leads_agendados = Lead.objects.filter(nombre_asesor__isnull=False, activo=True).order_by("-id")
        separados_y_facturados = VehiculosInteresLead.objects.filter(Q(separado=True) | Q(facturado=True)).values_list("lead").distinct()
        separados = VehiculosInteresLead.objects.filter(separado=True).values_list("lead").distinct()
        facturados = VehiculosInteresLead.objects.filter(facturado=True).values_list("lead").distinct()
        leads_facturados = Lead.objects.filter(pk__in=facturados, activo=True).order_by("-id")
        leads_separados = Lead.objects.filter(pk__in=separados, activo=True).order_by("-id")
        leads_separados_y_facturados = Lead.objects.filter(pk__in=separados_y_facturados, activo=True).order_by("-id")
        leads_desistidos = Lead.objects.filter(etapa="Desistido", activo=True).order_by("-id")

        historial = Historial.objects.filter(lead__in=leads_agendados).values("lead").annotate(Max("fecha"))

        print(historial)

        verificados = HistorialVerificaciones.objects.values("lead", "tipo_solicitud").distinct().order_by("-id")

        mostrado_marcas = VehiculosInteresLead.objects.filter(mostrado=True).values("lead").distinct().values("lead", "marca", "modelo", "codigo_vehiculo")
        separados_y_facturados_marcas = VehiculosInteresLead.objects.filter(mostrado=False).values("lead").distinct().values("lead", "marca", "modelo", "codigo_vehiculo")

        print(leads_separados_y_facturados)

        origenes_lead_agendados = leads_agendados.values("origen_lead")
        
        respuestas_agendados = leads_agendados.values("respuesta")
        respuestas_desistidos = leads_desistidos.values("respuesta")
        
        estados_agendados = leads_agendados.values("estado")
        estados_separados_y_facturados = leads_separados_y_facturados.values("estado")
        estados_desistidos = leads_desistidos.values("estado")

        anfitriones_agendados = leads_agendados.values("nombre_anfitrion")

        asesores_agendados = leads_agendados.values("nombre_asesor")
        asesores_separados_y_facturados = leads_separados_y_facturados.values("nombre_asesor")
        asesores_desistidos = leads_desistidos.values("nombre_asesor")

        salas_agendados = leads_agendados.values("sala")
        salas_separados_y_facturados = leads_separados_y_facturados.values("sala")
        salas_desistidos = leads_desistidos.values("sala")

        mostrado_marcas_agendados = VehiculosInteresLead.objects.filter(mostrado=True).filter(lead__in=leads_agendados).values("lead", "mostrado").distinct().annotate(latest=Max("id")).values("lead", "marca", "modelo")
        mostrado_marcas_separados_y_facturados = VehiculosInteresLead.objects.filter(mostrado=True).filter(lead__in=leads_separados_y_facturados).values("lead", "mostrado").distinct().annotate(latest=Max("id")).values("lead", "marca", "modelo")
        mostrado_marcas_desistidos = VehiculosInteresLead.objects.filter(mostrado=True).filter(lead__in=leads_desistidos).values("lead", "mostrado").distinct().annotate(latest=Max("id")).values("lead", "marca", "modelo")
       
        context["anfitriones_agendados"] = anfitriones_agendados
        context["asesor_actual"] = asesor_actual
        context["asesores_agendados"] = asesores_agendados
        context["asesores_separados_y_facturados"] = asesores_separados_y_facturados
        context["asesores_desistidos"] = asesores_desistidos
        context["calendario_general"] = calendario_general
        context["cantidad_agendados"] = leads_agendados.count()
        context["cantidad_desistidos"] = leads_desistidos.count()
        context["cantidad_historial"] = historial.count()
        context["cantidad_separados_y_facturados"] = leads_separados_y_facturados.count()
        context["estados_agendados"] = estados_agendados
        context["estados_separados_y_facturados"] = estados_separados_y_facturados
        context["estados_desistidos"] = estados_desistidos
        context["historial"] = historial
        context["leads_agendados"] = leads_agendados
        context["leads_desistidos"] = leads_desistidos
        context["leads_facturados"] = leads_facturados
        context["leads_separados"] = leads_separados
        context["leads_separados_y_facturados"] = leads_separados_y_facturados
        context["mostrado_marcas"] = mostrado_marcas
        context["mostrado_marcas_agendados"] = mostrado_marcas_agendados
        context["mostrado_marcas_separados_y_facturados"] = mostrado_marcas_separados_y_facturados
        context["mostrado_marcas_desistidos"] = mostrado_marcas_desistidos
        context["origenes_lead_agendados"] = origenes_lead_agendados
        context["respuestas_agendados"] = respuestas_agendados
        context["respuestas_desistidos"] = respuestas_desistidos
        context["salas_agendados"] = salas_agendados
        context["salas_separados_y_facturados"] = salas_separados_y_facturados
        context["salas_desistidos"] = salas_desistidos
        context["separados"] = separados
        context["separados_y_facturados_marcas"] = separados_y_facturados_marcas
        context["user"] = user
        context["verificados"] = verificados

        return context
    
class TiemposView(LoginRequiredMixin, TemplateView):
    # Vista de Tiempos

    template_name = "Tiempos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(username=self.request.user)
        try:
            asesor_actual = Asesor.objects.get(nombre=functions.separar_nombre(user.username))
        except:
            asesor_actual = {}
            asesor_actual["pk"] = 0
        print(user)

        calendario_general = True
        for grupo in self.request.user.groups.all():
            if grupo.name == "Asesor":
                calendario_general = False

        leads_tiempos = Lead.objects.filter(tiempo_primer_contacto__isnull=False, activo=True).order_by("-id")
        leads_verificados = Lead.objects.filter(estado_llamada_verificacion__isnull=False, activo=True).order_by("-id")

        verificados = HistorialVerificaciones.objects.values("lead", "tipo_solicitud").distinct().order_by("-id")

        mostrado_marcas = VehiculosInteresLead.objects.filter(mostrado=True).values("lead").distinct().values("lead", "marca", "modelo")

        print(verificados)
        print(mostrado_marcas)

        context["asesor_actual"] = asesor_actual
        context["calendario_general"] = calendario_general
        context["cantidad_tiempos"] = leads_tiempos.count()
        context["cantidad_verificados"] = leads_verificados.count()
        context["leads_tiempos"] = leads_tiempos
        context["leads_verificados"] = leads_verificados
        context["mostrado_marcas"] = mostrado_marcas
        context["user"] = user
        context["verificados"] = verificados

        return context
        
class AnuladosView(LoginRequiredMixin, TemplateView):
    # Vista de Anulados

    template_name = "Anulados.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(username=self.request.user)
        try:
            asesor_actual = Asesor.objects.get(nombre=functions.separar_nombre(user.username))
        except:
            asesor_actual = {}
            asesor_actual["pk"] = 0
        print(user)

        calendario_general = True
        for grupo in self.request.user.groups.all():
            if grupo.name == "Asesor":
                calendario_general = False

        leads_anulados = Lead.objects.filter(activo=False).order_by("-id")
        leads_verificados = Lead.objects.filter(estado_llamada_verificacion__isnull=False).order_by("-id")

        verificados = HistorialVerificaciones.objects.values("lead", "tipo_solicitud").distinct().order_by("-id")

        mostrado_marcas = VehiculosInteresLead.objects.filter(mostrado=True).values("lead").distinct().values("lead", "marca", "modelo")

        context["asesor_actual"] = asesor_actual
        context["calendario_general"] = calendario_general
        context["cantidad_anulados"] = leads_anulados.count()
        context["cantidad_verificados"] = leads_verificados.count()
        context["leads_anulados"] = leads_anulados
        context["leads_verificados"] = leads_verificados
        context["mostrado_marcas"] = mostrado_marcas
        context["user"] = user
        context["verificados"] = verificados

        return context
    
class ModernizeView(LoginRequiredMixin, TemplateView):
    # Vista de Modernize

    template_name = "Modernize.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(username=self.request.user)
        print(user)

        context["user"] = user

        return context
    
class Modernize2View(LoginRequiredMixin, TemplateView):
    # Vista de Modernize2

    template_name = "Modernize2.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(username=self.request.user)
        print(user)

        context["user"] = user

        return context
    
class ReportesEventosView(LoginRequiredMixin, TemplateView):
    # Vista de Reportes Eventos

    template_name = "ReportesEventos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(username=self.request.user)

        leads = Lead.objects.filter(activo=True, nombre_asesor__isnull=False).order_by("-id")

        functions.verificar_primer_contacto_todos_los_leads(leads)

        try:
            asesor_actual = Asesor.objects.get(nombre=functions.separar_nombre(user.username))
        except:
            asesor_actual = {}
            asesor_actual["pk"] = 0
        print(user)
        
        calendario_general = True
        for grupo in self.request.user.groups.all():
            if grupo.name == "Asesor":
                calendario_general = False

        leads_activos = Lead.objects.filter(activo=True)
        asesores = Asesor.objects.all()
        asesores_127 = Asesor.objects.filter(sala="127")
        asesores_morato = Asesor.objects.filter(sala="Morato")
        today_min = datetime.combine(timezone.now().date(), datetime.today().time().min)
        today_max = datetime.combine(timezone.now().date(), datetime.today().time().max)
        cantidad_hoy = Evento.objects.filter(fecha_hora__range=(today_min, today_max)).count()
        eventos_hoy = Evento.objects.filter(fecha_hora__range=(today_min, today_max)).values("asesor").annotate(cantidad=Count("pk"))
        cantidad_pendiente = Evento.objects.filter(fecha_hora__gt=today_max).count()
        eventos_pendientes = Evento.objects.filter(fecha_hora__gt=today_max).values("asesor").annotate(cantidad=Count("pk"))

        print(asesores)
        print("eventos_hoy")
        print(eventos_hoy)
        print(eventos_hoy.values("asesor"))

        print(eventos_pendientes)

        context["asesor_actual"] = asesor_actual
        context["asesores"] = asesores
        context["asesores_127"] = asesores_127
        context["asesores_morato"] = asesores_morato
        context["calendario_general"] = calendario_general
        context["cantidad_activos"] = leads_activos.count()
        context["cantidad_hoy"] = cantidad_hoy
        context["cantidad_pendientes"] = cantidad_pendiente
        context["eventos_hoy"] = eventos_hoy
        context["eventos_pendientes"] = eventos_pendientes
        context["leads_activos"] = leads_activos
        context["user"] = user

        return context
    
    def post(self, request):

        user = User.objects.get(username=self.request.user)
        if request.POST.get("EventoNombre"):

            nombre = request.POST.get("EventoNombre")
            tipo = request.POST.get("EventoTipo")
            telefono_cliente = request.POST.get("EventoTelefono")
            observaciones = request.POST.get("EventoObservaciones")
            asesor = request.POST.get("EventoAsesor")
            fecha_hora = request.POST.get("EventoFechaHora")
            
            evento = Evento.objects.create(nombre=nombre,
                                           tipo=tipo,
                                           telefono_cliente=telefono_cliente,
                                           observaciones=observaciones,
                                           asesor=Asesor.objects.get(nombre=asesor),
                                           fecha_hora=datetime.strptime(fecha_hora,"%Y-%m-%dT%H:%M"),
                                           lead=Lead.objects.get(id=21)
                                           )
            return JsonResponse(evento.pk, safe=False)

class CalendarView(LoginRequiredMixin, TemplateView):
    # Vista de Calendar

    template_name = "Calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(username=self.request.user)
        try:
            asesor_actual = Asesor.objects.get(nombre=functions.separar_nombre(user.username))
        except:
            asesor_actual = {}
            asesor_actual["pk"] = 0

        calendario_general = True
        for grupo in self.request.user.groups.all():
            if grupo.name == "Asesor":
                calendario_general = False

        asesores = Asesor.objects.all()

        eventos = Evento.objects.all()

        today_min = datetime.combine(timezone.now().date(), datetime.today().time().min)
        today_max = datetime.combine(timezone.now().date(), datetime.today().time().max)
        cantidad_hoy = Evento.objects.filter(fecha_hora__range=(today_min, today_max)).count()
        eventos_hoy = Evento.objects.filter(fecha_hora__range=(today_min, today_max)).values("asesor").annotate(cantidad=Count("pk"))
        cantidad_pendiente = Evento.objects.filter(fecha_hora__gt=today_max).count()
        eventos_pendientes = Evento.objects.filter(fecha_hora__gt=today_max).values("asesor").annotate(cantidad=Count("pk"))


        etapas = CatalogoRespuestasByEtapa.objects.values("etapa").distinct()
        respuestas = CatalogoRespuestasByEtapa.objects.values("respuesta").distinct()

        print(user)

        print(eventos_hoy)
        print(eventos_pendientes)

        general = True

        prospectos = Prospecto.objects.all()

        context["asesor_actual"] = asesor_actual
        context["asesores"] = asesores
        context["calendario_general"] = calendario_general
        context["cantidad_hoy"] = cantidad_hoy
        context["cantidad_pendientes"] = cantidad_pendiente
        context["etapas"] = etapas
        context["eventos"] = eventos
        context["eventos_hoy"] = eventos_hoy
        context["eventos_pendientes"] = eventos_pendientes
        context["general"] = general
        context["prospectos"] = prospectos
        context["respuestas"] = respuestas
        context["user"] = user

        return context

    def post(self, request):
        r = request.POST
        user = User.objects.get(username=self.request.user)
        
        print(r)
        if r.get("nombre_evento", None):
            nombre = r.get("nombre_evento", None)
            tipo = r.get("tipo", None)
            telefono_cliente = r.get("telefono_cliente", None)
            observaciones = r.get("observaciones", None)
            asesor = r.get("asesor", None)
            fecha_hora = r.get("fecha_hora", None)

            lead = Lead.objects.get(prospecto__celular=telefono_cliente)
            evento = Evento.objects.create(nombre=nombre,
                                           tipo=tipo,
                                           telefono_cliente=telefono_cliente,
                                           observaciones=observaciones,
                                           asesor=Asesor.objects.get(nombre=asesor),
                                           fecha_hora=datetime.strptime(fecha_hora,"%Y-%m-%dT%H:%M"),
                                           lead=lead
                                           )

            return HttpResponseRedirect(reverse_lazy('dashboards:calendar'))

        if r.get("title", None):
            nombre = r.get("title", None)
            evento = Evento.objects.get(nombre=nombre)
            evento.delete()

            return HttpResponseRedirect(reverse_lazy('dashboards:calendar'))
        if r.get("title2", None):
            nombre = r.get("title2", None)
            evento = Evento.objects.get(nombre=nombre).lead.pk
            
            print(evento)

            return JsonResponse(evento, safe=False)
        if r.get("title_cumplido", None):
            nombre = r.get("title_cumplido", None)
            evento = Evento.objects.get(nombre=nombre)
            evento.cumplido = True
            evento.fecha_hora_cumplido = datetime.now()
            evento.save()
            
            return HttpResponseRedirect(reverse_lazy('dashboards:calendar'))


class CalendarDetailView(LoginRequiredMixin, DetailView):
    # Vista de Calendar Detail

    template_name = "Calendar.html"
    slug_field = "adviser"
    slug_url_kwarg = "adviser"
    queryset = Asesor.objects.all()
    context_object_name = "adviser"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        adviser = self.get_object()
        user = User.objects.get(username=self.request.user)
        try:
            asesor_actual = Asesor.objects.get(nombre=functions.separar_nombre(user.username))
        except:
            asesor_actual = {}
            asesor_actual["pk"] = 0

        calendario_general = True
        for grupo in self.request.user.groups.all():
            if grupo.name == "Asesor":
                calendario_general = False

        asesores = Asesor.objects.all()

        eventos = Evento.objects.filter(asesor=adviser)

        today_min = datetime.combine(timezone.now().date(), datetime.today().time().min)
        today_max = datetime.combine(timezone.now().date(), datetime.today().time().max)
        cantidad_hoy = Evento.objects.filter(fecha_hora__range=(today_min, today_max)).count()
        eventos_hoy = Evento.objects.filter(fecha_hora__range=(today_min, today_max)).values("asesor").annotate(cantidad=Count("pk"))
        cantidad_pendiente = Evento.objects.filter(fecha_hora__gt=today_max).count()
        eventos_pendientes = Evento.objects.filter(fecha_hora__gt=today_max).values("asesor").annotate(cantidad=Count("pk"))

        etapas = CatalogoRespuestasByEtapa.objects.values("etapa").distinct()
        respuestas = CatalogoRespuestasByEtapa.objects.values("respuesta").distinct()

        print(user)
        print(adviser.pk)

        mostrar_evento = False
        for grupo in self.request.user.groups.all():
            if grupo.name == "Asesor":
                mostrar_evento = True

        general = False

        prospectos = eventos.values("telefono_cliente").distinct()

        print(prospectos)

        context["adviser"] = adviser
        context["asesor_actual"] = asesor_actual
        context["asesores"] = asesores
        context["calendario_general"] = calendario_general
        context["cantidad_hoy"] = cantidad_hoy
        context["cantidad_pendientes"] = cantidad_pendiente
        context["etapas"] = etapas
        context["eventos"] = eventos
        context["eventos_hoy"] = eventos_hoy
        context["eventos_pendientes"] = eventos_pendientes
        context["general"] = general
        context["mostrar_evento"] = mostrar_evento
        context["prospectos"] = prospectos
        context["respuestas"] = respuestas
        context["user"] = user

        return context

    def post(self, request, pk):
        r = request.POST
        user = User.objects.get(username=self.request.user)
        
        print(r)
        if r.get("nombre_evento", None):
            nombre = r.get("nombre_evento", None)
            tipo = r.get("tipo", None)
            telefono_cliente = r.get("telefono_cliente", None)
            observaciones = r.get("observaciones", None)
            asesor = r.get("asesor", None)
            fecha_hora = r.get("fecha_hora", None)
            
            print(telefono_cliente)
            print(asesor)
            print(type(telefono_cliente))

            lead = Lead.objects.get(prospecto__celular=telefono_cliente)
            evento = Evento.objects.create(nombre=nombre,
                                           tipo=tipo,
                                           telefono_cliente=telefono_cliente,
                                           observaciones=observaciones,
                                           asesor=Asesor.objects.get(nombre=asesor),
                                           fecha_hora=datetime.strptime(fecha_hora,"%Y-%m-%dT%H:%M"),
                                           lead=lead
                                           )

            return HttpResponseRedirect(reverse_lazy('dashboards:calendar_detail', kwargs={"pk": pk}))
        if r.get("title2", None):
            nombre = r.get("title2", None)
            evento = Evento.objects.get(nombre=nombre).lead.pk
            
            return JsonResponse(evento, safe=False)
        if r.get("title_cumplido", None):
            nombre = r.get("title_cumplido", None)
            evento = Evento.objects.get(nombre=nombre)
            evento.cumplido = True
            evento.fecha_hora_cumplido = datetime.now()
            evento.save()
            
            return HttpResponseRedirect(reverse_lazy('dashboards:calendar_detail', kwargs={"pk": pk}))