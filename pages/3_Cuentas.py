import streamlit as st
import pandas as pd
import calendar
from sqlalchemy import create_engine

user     = st.secrets["user_bigdata"]
password = st.secrets["password_bigdata"]
host     = st.secrets["host_bigdata"]
schema   = 'partyplum'

engine          = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
datafacturacion = pd.read_sql_query(f"SELECT * FROM partyplum._facturacion;" , engine)
datapagos       = pd.read_sql_query(f"SELECT * FROM partyplum._pagos_recibidos;" , engine)
engine.dispose()

diccionario = {'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo', 'April': 'Abril', 'May': 'Mayo', 'June': 'Junio', 'July': 'Julio', 'August': 'Agosto', 'September': 'Septiembre', 'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'}
datafacturacion['mesevento'] = datafacturacion['fecha_evento'].apply(lambda x: diccionario[calendar.month_name[x.month]])

w         = datapagos.groupby(['id_facturacion'])['valor'].sum().reset_index()
w.columns = ['id','valor del pago']
datafacturacion = datafacturacion.merge(w,on='id',how='left',validate='1:1')

datafacturacion = datafacturacion.sort_values(by=['fecha_evento','nombre_cliente'],ascending=True)
datafacturacion.rename(columns={'mesevento': 'MES DE EVENTO', 'realizado': 'EVENTO REALIZADO', 'fecha_evento': 'FECHA EVENTO', 'nombre_cliente': 'CLIENTE', 'valor del pago': 'VALOR DEL PAGO', 'factura': 'FACTURA', 'fecha_factura': 'FECHA FACTURA', 'paquete': 'PAQUETE', 'valor_factura': 'VALOR FACTURA', 'valor_proveedores': 'PROVEEDORES', 'ganancia_founder': 'GANANCIA VIVI', 'ganancia_pp_siniva': 'GANANCIA PARTY PLUM SIN IVA', 'iva_pp': 'IVA GANANCIA PARTY PLUM', 'recaudo_terceros': 'RECAUDO INGRESO A TERCEROS', 'tipocliente': 'TIPO PERSONA', 'tipo_identificacion': 'TIPO DOCUMENTO', 'identificacion': 'CEDULA', 'razonsocial': 'RAZON SOCIAL', 'email': 'EMAIL', 'telefono': 'CELULAR', 'direccion_evento': 'DIRECCION DEL EVENTO', 'ciudad_evento': 'CIUDAD DEL EVENTO', 'link_factura': 'LINK FACTURA', 'devolucion': 'DEVOLUCIÓN', 'valor_devolucion': 'VALOR DEVOLUCIÓN', 'fecha_devolucion': 'FECHA DEVOLUCIÓN', 'observaciones': 'OBSERVACIONES'},inplace=True)
variables       = ['MES DE EVENTO', 'EVENTO REALIZADO', 'FECHA EVENTO', 'CLIENTE', 'VALOR DEL PAGO', 'FACTURA', 'FECHA FACTURA', 'PAQUETE', 'VALOR FACTURA', 'PROVEEDORES', 'GANANCIA VIVI', 'GANANCIA PARTY PLUM SIN IVA', 'IVA GANANCIA PARTY PLUM', 'RECAUDO INGRESO A TERCEROS', 'TIPO PERSONA', 'TIPO DOCUMENTO', 'CEDULA', 'RAZON SOCIAL', 'EMAIL', 'CELULAR', 'DIRECCION DEL EVENTO', 'CIUDAD DEL EVENTO', 'LINK FACTURA', 'DEVOLUCIÓN', 'VALOR DEVOLUCIÓN', 'FECHA DEVOLUCIÓN', 'OBSERVACIONES']
datafacturacion = datafacturacion[variables]

datafacturacion.to_excel(r'D:\Dropbox\Empresa\Matina Eventos\ADMINISTRATIVA\1_CUENTAS\Export_Cuentas_Agregadas.xlsx')