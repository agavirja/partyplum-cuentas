import streamlit as st
import pandas as pd
import pymysql
import boto3
from datetime import datetime
from sqlalchemy import create_engine 
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, ColumnsAutoSizeMode, AgGridTheme
from st_aggrid.shared import JsCode
from bs4 import BeautifulSoup

from display.style_white import style 

st.set_page_config(layout='wide')

def main():
       
    #-------------------------------------------------------------------------#
    # Variables
    formato = {
               'showevent':False,
               }
    
    for key,value in formato.items():
        if key not in st.session_state: 
            st.session_state[key] = value
            
    IVA = 0.19
    col1,col2 = st.columns([0.8,0.2])
    with col2:
        st.image('https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/partyplum_logosimbolo.png',width=200)

    style()
      
    with st.spinner('Buscando información'):
        dataclientes = getclientes()
    
    col1, col2 = st.columns(2)
    with col1:
        options = list(dataclientes[dataclientes['nombre_cliente'].notnull()]['nombre_cliente'].unique())+list(dataclientes[dataclientes['razonsocial'].notnull()]['razonsocial'].unique())
        options = ['']+list(sorted(options))
        cliente = st.selectbox('Seleccionar cliente:',options=options)
    
    #-------------------------------------------------------------------------#
    # Clientes
    if cliente=='':
        titulo = 'Crear nuevo cliente'
        html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Título Centrado</title></head><body><section style="text-align: center;"><h1 style="color: #fff; font-size: 20px; font-family: Arial, sans-serif; font-weight: bold; background-color: #9D57BA; padding: 10px;">{titulo}</h1></section></body></html>"""
        texto = BeautifulSoup(html, 'html.parser')
        st.markdown(str(texto), unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            newclient = st.toggle('Crear nuevo cliente',value=False)
        registrarcliente(newclient)
        
    #-------------------------------------------------------------------------#
    # Facturas
    data2filtros = pd.DataFrame()
    
    if cliente!='':
        with st.spinner('Datos del evento'):
            dataeventos  = geteventos(cliente)
            
        titulo = 'Crear evento para el cliente'
        html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Título Centrado</title></head><body><section style="text-align: center;"><h1 style="color: #fff; font-size: 20px; font-family: Arial, sans-serif; font-weight: bold; background-color: #9D57BA; padding: 10px;">{titulo}</h1></section></body></html>"""
        texto = BeautifulSoup(html, 'html.parser')
        st.markdown(str(texto), unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        valueE       = False
        titulotoggle = 'Crear nuevo evento'
        if dataeventos.empty: 
            valueE       = True
            titulotoggle = 'Crear evento'
            
        with col1:
            newevent = st.toggle(titulotoggle,value=valueE)
            df       = dataclientes[(dataclientes['nombre_cliente']==cliente) | (dataclientes['razonsocial']==cliente)].iloc[[0]]
        crearevento(newevent,df)

        data2filtros = dataeventos.copy()
        if len(dataeventos)>1:
            titulo = 'Información de los eventos'
            html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Título Centrado</title></head><body><section style="text-align: center;"><h1 style="color: #fff; font-size: 20px; font-family: Arial, sans-serif; font-weight: bold; background-color: #9D57BA; padding: 10px;">{titulo}</h1></section></body></html>"""
            texto = BeautifulSoup(html, 'html.parser')
            st.markdown(str(texto), unsafe_allow_html=True)
            st.write('')
            st.write('')
            
            df        = dataeventos.copy()
            variables = ['id','fecha_evento','realizado','paquete','factura','link_factura','valor_factura','valor_proveedores','ganancia_founder','ganancia_pp_siniva','iva_pp','ganancia_pp','recaudo_terceros']
            variables = [x for x in variables if x in df]
            df        = df[variables]
            df.rename(columns={'link_factura':'link'},inplace=True)
            gb = GridOptionsBuilder.from_dataframe(df,editable=True)
            gb.configure_selection(selection_mode="multiple", use_checkbox=True)
            cell_renderer =  JsCode("""function(params) {return `<a href=${params.value} target="_blank">${params.value}</a>`}""")
            
            gb.configure_column(
                "link",
                headerName="link",
                width=100,
                cellRenderer=JsCode("""
                    class UrlCellRenderer {
                      init(params) {
                        this.eGui = document.createElement('a');
                        this.eGui.innerText = 'Link';
                        this.eGui.setAttribute('href', params.value);
                        this.eGui.setAttribute('style', "text-decoration:none");
                        this.eGui.setAttribute('target', "_blank");
                      }
                      getGui() {
                        return this.eGui;
                      }
                    }
                """)
            )

            response = AgGrid(df,
                        gridOptions=gb.build(),
                        columns_auto_size_mode="FIT_CONTENTS",
                        theme=AgGridTheme.STREAMLIT,
                        updateMode=GridUpdateMode.VALUE_CHANGED,
                        allow_unsafe_jscode=True,
                        height=200)
        
            df = pd.DataFrame(response['selected_rows'])
            if not df.empty:
                data2filtros = dataeventos[dataeventos['id'].isin(df['id'])]

    #-------------------------------------------------------------------------#
    # Editar cifras de facturas
    if not data2filtros.empty and len(data2filtros)==1:
        
        # Ya se emitio factura
        data2filtros.index = range(len(data2filtros))
        if isinstance(data2filtros['link_factura'].iloc[0],str):
            st.session_state.showevent = True
        
        titulo = 'Cifras generales del evento'
        html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Título Centrado</title></head><body><section style="text-align: center;"><h1 style="color: #fff; font-size: 20px; font-family: Arial, sans-serif; font-weight: bold; background-color: #9D57BA; padding: 10px;">{titulo}</h1></section></body></html>"""
        texto = BeautifulSoup(html, 'html.parser')
        st.markdown(str(texto), unsafe_allow_html=True)
        st.write('')
        st.write('')
        
        dataexport = data2filtros.copy()
        dataexport.index = range(len(dataexport))
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            default_value = dataexport['fecha_evento'].iloc[0]
            fecha_evento  = st.date_input('Fecha de evento', value=default_value)
            dataexport.loc[0, 'fecha_evento'] = fecha_evento

        with col2:
            options = ['Bogota','Agua de Dios', 'Albán', 'Anapoima', 'Anolaima', 'Apulo', 'Arbeláez', 'Beltrán', 'Bituima', 'Bojacá', 'Cabrera', 'Cachipay', 'Cajicá', 'Caparrapí', 'Cáqueza', 'Carmen de Carupa', 'Chaguaní', 'Chía', 'Chipaque', 'Choachí', 'Chocontá', 'Cogua', 'Cota', 'Cucunubá', 'El Colegio', 'El Peñón', 'El Rosal', 'Facatativá', 'Fómeque', 'Fosca', 'Funza', 'Fúquene', 'Fusagasugá', 'Gachalá', 'Gachancipá', 'Gachetá', 'Gama', 'Girardot', 'Granada', 'Guachetá', 'Guaduas', 'Guasca', 'Guataquí', 'Guatavita', 'Guayabal de Síquima', 'Guayabetal', 'Gutiérrez', 'Jerusalén', 'Junín', 'La Calera', 'La Mesa', 'La Palma', 'La Peña', 'La Vega', 'Lenguazaque', 'Machetá', 'Madrid', 'Manta', 'Medina', 'Mosquera', 'Nariño', 'Nemocón', 'Nilo', 'Nimaima', 'Nocaima', 'Pacho', 'Paime', 'Pandi', 'Paratebueno', 'Pasca', 'Puerto Salgar', 'Pulí', 'Quebradanegra', 'Quetame', 'Quipile', 'Ricaurte', 'San Antonio del Tequendama', 'San Bernardo', 'San Cayetano', 'San Francisco', 'San Juan de Río Seco', 'Sasaima', 'Sesquilé', 'Sibaté', 'Silvania', 'Simijaca', 'Soacha', 'Sopó', 'Subachoque', 'Suesca', 'Supatá', 'Susa', 'Sutatausa', 'Tabio', 'Tausa', 'Tena', 'Tenjo', 'Tibacuy', 'Tibirita', 'Tocaima', 'Tocancipá', 'Topaipí', 'Ubalá', 'Ubaque', 'Une', 'Útica', 'Venecia', 'Vergara', 'Vianí', 'Villagómez', 'Villapinzón', 'Villeta', 'Viotá', 'Yacopí', 'Zipacón', 'Zipaquirá']
            value   = dataexport['ciudad_evento'].iloc[0]
            index   = 0
            if value is not None and value!='':
                index = options.index(value)
            ciudad_evento = st.selectbox('Ciudad del evento: ',options=options,index=index)
            dataexport.loc[0,'ciudad_evento'] = ciudad_evento
            
        with col3:
            default_value    = dataexport['direccion_evento'].iloc[0]
            direccion_evento = st.text_input('Dirección del evento: ', value=default_value)
            dataexport.loc[0, 'direccion_evento'] = direccion_evento

        with col4:
            options = ['DECORACION PLUM MINI TABLE','DECORACION PLUM MEDIANO','DECORACION PLUM DELUXE','DECORACION PLUM SPLENDOR','DECORACION PLUM ECOLOGICO']
            value   = dataexport['paquete'].iloc[0]
            index   = 0
            if value is not None and value!='':
                index = options.index(value)
            paquete = st.selectbox('Paquete: ',options=options,index=index)
            dataexport.loc[0,'paquete'] = paquete
            
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.write('')
            st.write('')
            default_value = dataexport['realizado'].iloc[0]
            realizado = st.toggle('Evento realizado ', value=bool(default_value))
            dataexport.loc[0, 'realizado'] = realizado
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            default_value = dataexport['valor_factura'].iloc[0]
            valor_factura = st.number_input('Valor factura: ', value=default_value,format="%f")
            dataexport.loc[0, 'valor_factura'] = valor_factura
        
        with col2:
            default_value     = dataexport['valor_proveedores'].iloc[0]
            valor_proveedores = st.number_input('Valor proveedores: ', value=default_value,format="%f")
            dataexport.loc[0, 'valor_proveedores'] = valor_proveedores
        
        with col3:
            default_value = dataexport['ganancia_pp'].iloc[0]
            ganancia_pp = st.number_input('Ganancia pp: ', value=default_value,format="%f")
            dataexport.loc[0, 'ganancia_pp'] = ganancia_pp
            
        with col4:
            valor            = valor_factura-valor_proveedores-ganancia_pp
            ganancia_founder = st.number_input('Ganancia founder: ', value=valor,disabled=True,format="%f")
            dataexport.loc[0, 'ganancia_founder'] = ganancia_founder
            
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            value              = ganancia_pp/(1+IVA)
            ganancia_pp_siniva = st.number_input('Ganancia pp sin iva: ', value=value,disabled=True,format="%f")
            dataexport.loc[0, 'ganancia_pp_siniva'] = ganancia_pp_siniva
            
        with col2:
            value         = ganancia_pp*IVA
            iva_pp        = st.number_input('Iva pp: ', value=value,disabled=True,format="%f")
            dataexport.loc[0, 'iva_pp'] = iva_pp
        
        with col3:
            valor            = valor_proveedores+ganancia_founder
            recaudo_terceros = st.number_input('Recaudo_terceros: ', value=valor,disabled=True,format="%f")
            dataexport.loc[0, 'recaudo_terceros'] = recaudo_terceros
        
        with col4:
            default_value  = dataexport['observaciones'].iloc[0]
            observaciones = st.text_area('Observaciones: ', value=default_value)
            dataexport.loc[0, 'observaciones'] = observaciones
        
        
        
        col1,col2,col3,col4 = st.columns(4)
        with col1:
            default_value = dataexport['valor_total_cuenta_personal'].iloc[0]
            valor_total_cuenta_personal = st.number_input('Valor transferencia cuenta personal:', value=default_value,format="%f")
            dataexport.loc[0, 'valor_total_cuenta_personal'] = valor_total_cuenta_personal
        with col2:
            options = ['','Bancolombia','PNC']
            value   = dataexport['paquete'].iloc[0]
            index   = 0
            if value is not None and value!='':
                try: index = options.index(value)
                except: pass
            tipo_cuenta_personal = st.selectbox('Tipo de la cuenta personal:',options=options,index=index)
            if tipo_cuenta_personal=='': tipo_cuenta_personal = None
            dataexport.loc[0,'tipo_cuenta_personal'] = tipo_cuenta_personal

            tipo_moneda_cuenta_personal = None
            if  tipo_cuenta_personal=='': 
                tipo_cuenta_personal = None
            elif 'Bancolombia' in tipo_cuenta_personal :
                tipo_moneda_cuenta_personal = 'COP'
            elif 'PNC' in tipo_cuenta_personal :
                tipo_moneda_cuenta_personal = 'USD'
            dataexport.loc[0,'tipo_moneda_cuenta_personal'] = tipo_moneda_cuenta_personal

        with col3:
            default_value = dataexport['fecha_pago_cuenta_personal'].iloc[0]
            fecha_pago_cuenta_personal  = st.date_input('Fecha de la transferencia a cuenta personal:', value=default_value)
            dataexport.loc[0, 'fecha_pago_cuenta_personal'] = fecha_pago_cuenta_personal

        with col4:
            default_value = dataexport['tasa_cambio_moneda_cuenta_personal'].iloc[0]
            tasa_cambio_moneda_cuenta_personal = st.number_input('Tasa de cambio transferencia cuenta personal:', value=default_value,format="%f")
            dataexport.loc[0, 'tasa_cambio_moneda_cuenta_personal'] = tasa_cambio_moneda_cuenta_personal

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.write('')
            st.write('')
            default_value = dataexport['devolucion'].iloc[0]
            devolucion    = st.toggle('Devolucion: ', value=bool(default_value))
            dataexport.loc[0, 'devolucion'] = devolucion
        
        with col2:
            if devolucion:
                default_value    = dataexport['valor_devolucion'].iloc[0]
                default_value    = int(default_value) if isinstance(default_value, int) else 0
                valor_devolucion = st.number_input('Valor devolución: ', value=int(default_value))
                dataexport.loc[0, 'valor_devolucion'] = valor_devolucion

        with col3:
            if devolucion:
                default_value    = dataexport['fecha_devolucion'].iloc[0]
                try:    fecha_devolucion = st.date_input('Fecha devolución: ', value=default_value)
                except: fecha_devolucion = st.date_input('Fecha devolución: ', value=None)
                dataexport.loc[0, 'fecha_devolucion'] = fecha_devolucion
            
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            default_value = dataexport['fecha_factura'].iloc[0]
            fecha_evento  = st.date_input('Fecha dela factura', value=default_value)
            dataexport.loc[0, 'fecha_factura'] = fecha_evento
        
        with col2:
            uploaded_file  = st.file_uploader("Subir factura ")
            link_factura   = dataexport['link_factura'].iloc[0]
            if isinstance(link_factura,str):
                st.write(link_factura)

        with col3:
            if uploaded_file:
                st.write('')
                st.write('')
                if st.button('Subir factura'):
                    link_factura = uploadfileS3('facturas',uploaded_file, f'factura_id_{dataexport["id"].iloc[0]}')
                    st.rerun()
                link_factura = getfileS3('facturas',f'factura_id_{dataexport["id"].iloc[0]}.pdf')
            dataexport.loc[0, 'link_factura'] = link_factura
        
        with col4:
            st.write('')
            st.write('')
            default_value = dataexport['factura'].iloc[0]
            if isinstance(link_factura,str):
                default_value = True
            factura = st.toggle('Factura ', value=bool(default_value))
            dataexport.loc[0, 'factura'] = factura
            
        col1,col2 = st.columns([0.3,0.7])
        with col1:
            if st.button('Guardar '):
                with st.spinner('Guardando datos de evento y factura'):
                    edit_factura(dataexport,'_facturacion')
        
        colI1,colI2 = st.columns([0.95,0.05])
    #-------------------------------------------------------------------------#
    # Pagos recibidos
    datapagosfiltro = pd.DataFrame()
    if not data2filtros.empty and len(data2filtros)==1:
        titulo = 'Reportar un nuevo pago'
        html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Título Centrado</title></head><body><section style="text-align: center;"><h1 style="color: #fff; font-size: 20px; font-family: Arial, sans-serif; font-weight: bold; background-color: #9D57BA; padding: 10px;">{titulo}</h1></section></body></html>"""
        texto = BeautifulSoup(html, 'html.parser')
        st.markdown(str(texto), unsafe_allow_html=True)
        st.write('')
        st.write('')
        
        dataexport       = data2filtros.copy()
        dataexport.index = range(len(dataexport))
        col1, col2 = st.columns(2)
        with col1:
            newpay = st.toggle('Crear nuevo pago',value=False)
        if newpay:
            crearpago(dataexport)

        with st.spinner('Datos del evento'):
            datapagos = getpayments(dataexport['id'].iloc[0])
            variablesdrop = [x for x in ['fecha_registro','id_facturacion'] if x in datapagos]
            if variablesdrop!=[]:
                datapagos.drop(columns=variablesdrop,inplace=True)
            recaudototal = datapagos['valor'].sum()
            if not datapagos.empty:
                titulo = 'Información de pagos'
                html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Título Centrado</title></head><body><section style="text-align: center;"><h1 style="color: #fff; font-size: 20px; font-family: Arial, sans-serif; font-weight: bold; background-color: #9D57BA; padding: 10px;">{titulo}</h1></section></body></html>"""
                texto = BeautifulSoup(html, 'html.parser')
                st.markdown(str(texto), unsafe_allow_html=True)
                st.write('')
                st.write('')

                df         = datapagos.copy()
                #variables = ['id','fecha_evento','realizado','paquete','factura','link_factura','valor_factura','valor_proveedores','ganancia_founder','ganancia_pp_siniva','iva_pp','ganancia_pp','recaudo_terceros']
                #variables = [x for x in variables if x in df]
                #df        = df[variables]
                df.rename(columns={'comprobante':'link'},inplace=True)
                gb = GridOptionsBuilder.from_dataframe(df,editable=True)
                gb.configure_selection(selection_mode="multiple", use_checkbox=True)
                cell_renderer =  JsCode("""function(params) {return `<a href=${params.value} target="_blank">${params.value}</a>`}""")
                
                gb.configure_column(
                    "link",
                    headerName="link",
                    width=100,
                    cellRenderer=JsCode("""
                        class UrlCellRenderer {
                          init(params) {
                            this.eGui = document.createElement('a');
                            this.eGui.innerText = 'Link';
                            this.eGui.setAttribute('href', params.value);
                            this.eGui.setAttribute('style', "text-decoration:none");
                            this.eGui.setAttribute('target', "_blank");
                          }
                          getGui() {
                            return this.eGui;
                          }
                        }
                    """)
                )

                response = AgGrid(df,
                            gridOptions=gb.build(),
                            columns_auto_size_mode="FIT_CONTENTS",
                            theme=AgGridTheme.STREAMLIT,
                            updateMode=GridUpdateMode.VALUE_CHANGED,
                            allow_unsafe_jscode=True,
                            height=200)

                df = pd.DataFrame(response['selected_rows'])
                if not df.empty:
                    datapagosfiltro = datapagos[datapagos['id'].isin(df['id'])]

    #-------------------------------------------------------------------------#
    # Editar cifras de pagos
    if not datapagosfiltro.empty and len(datapagosfiltro)==1:
        titulo = 'Editar cifras de pagos'
        html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Título Centrado</title></head><body><section style="text-align: center;"><h1 style="color: #fff; font-size: 20px; font-family: Arial, sans-serif; font-weight: bold; background-color: #9D57BA; padding: 10px;">{titulo}</h1></section></body></html>"""
        texto = BeautifulSoup(html, 'html.parser')
        st.markdown(str(texto), unsafe_allow_html=True)
        st.write('')
        st.write('')

        dataexport       = datapagosfiltro.copy()
        dataexport.index = range(len(dataexport))

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            default_value = dataexport['fecha_pago'].iloc[0]
            try:    fecha_pago    = st.date_input('Fecha de pago', value=default_value)
            except: fecha_pago    = st.date_input('Fecha de pago', value=None)
            dataexport.loc[0, 'fecha_pago'] = fecha_pago
            
        with col2:
            options = ['ANTICIPO','PAGO FINAL'] 
            value   = dataexport['tipo_pago'].iloc[0]
            index   = 0
            if value is not None and value!='':
                index = options.index(value)
            tipo_pago = st.selectbox('Tipo de pago: ',options=options,index=index)
            dataexport.loc[0,'tipo_pago'] = tipo_pago
        with col3:
            options = ['TRANSFERENCIA','EFECTIVO','CONSIGNACION']
            value   = dataexport['forma_pago'].iloc[0]
            index   = 0
            if value is not None and value!='':
                index = options.index(value)
            forma_pago = st.selectbox('Forma de pago: ',options=options,index=index)
            dataexport.loc[0,'forma_pago'] = forma_pago
            
        with col4:
            default_value = dataexport['valor'].iloc[0]
            valor         = st.number_input('Valor: ', value=int(default_value))
            dataexport.loc[0, 'valor'] = valor

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            uploaded_file = st.file_uploader("Subir comprobante de pago ")
            comprobante   = dataexport['comprobante'].iloc[0]
            if isinstance(comprobante,str):
                st.write(comprobante)

        with col2:
            if uploaded_file:
                st.write('')
                st.write('')
                if st.button('Subir comprobante de pago'):
                    comprobante = uploadfileS3('pagos-recibidos',uploaded_file, f'pago_recibido_id_{dataexport["id"].iloc[0]}')
                    st.rerun()
                comprobante = getfileS3('pagos-recibidos',f'pago_recibido_id_{dataexport["id"].iloc[0]}.pdf')
            dataexport.loc[0, 'comprobante'] = comprobante
                
        col1,col2 = st.columns([0.3,0.7])
        with col1:
            if st.button('Guardar pago '):
                with st.spinner('Guardando datos de pago '):
                    edit_factura(dataexport,'_pagos_recibidos')
                
                
    #-------------------------------------------------------------------------#
    # Check de valores
    try:
        neto = int(valor_factura-recaudototal)
        with colI1:
            if neto==0: st.success("Las cifras cuadran!!!")
            else: st.error("El valor de la factura aún no cuadra con los pagos del cliente !!!")
        if neto==0: st.success("Las cifras cuadran!!!")
        else: st.error("El valor de la factura aún no cuadra con los pagos del cliente !!!")
        
    except: pass

@st.cache_data(show_spinner=False)
def getclientes():
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata"]
    schema   = 'partyplum'
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    data     = pd.read_sql_query("SELECT * FROM partyplum._clientes" , engine)
    engine.dispose()
    return data

@st.cache_data(show_spinner=False)
def geteventos(cliente):
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata"]
    schema   = 'partyplum'
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    data     = pd.read_sql_query(f"SELECT * FROM partyplum._facturacion WHERE nombre_cliente='{cliente}' or razonsocial='{cliente}'" , engine)
    engine.dispose()
    return data

@st.cache_data(show_spinner=False)
def getpayments(idfactura):
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata"]
    schema   = 'partyplum'
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    data     = pd.read_sql_query(f"SELECT * FROM partyplum._pagos_recibidos WHERE id_facturacion={idfactura}" , engine)
    engine.dispose()
    return data

def registrarcliente(newclient):
    if newclient:
        st.write('---')
        col1,col2,col3,col4 = st.columns(4)
        razonsocial = None
        with col1:
            tipocliente = st.selectbox('Tipo del cliente:',options=['Natural','Juridica'])
        if 'Natural' in tipocliente:
            with col2:
                tipo_identificacion = st.selectbox('Tipo de documento:',options=['CC','CE'])
        elif 'Juridica' in tipocliente:
            with col2:
                tipo_identificacion = st.selectbox('Tipo de documento:',options=['NIT'])
            with col4:
                razonsocial = st.text_input('Razón social:',value='').upper().strip()
        with col3:
            identificacion = st.text_input('Identificación:',value='')
        with col4:
            nombre_cliente = st.text_input('Nombre del cliente:',value='').upper().strip()
        with col1:
            telefono = st.text_input('Teléfono:',value='')
        with col2:
            email = st.text_input('Email:',value='')
        
        df = pd.DataFrame([{'tipocliente':tipocliente,'tipo_identificacion':tipo_identificacion,'razonsocial':razonsocial,'identificacion':identificacion,'nombre_cliente':nombre_cliente,'telefono':telefono,'email':email}])
        df['fecha_registro'] = datetime.now().strftime('%Y-%m-%d')
        df['available']      = 1
        if nombre_cliente!='' and tipo_identificacion!='' and identificacion!='':
            col1,col2 = st.columns([0.3,0.7])
            with col1:
                if st.button('Guardar cliente'):
                    with st.spinner('Guardando cliente'):
                        user      = st.secrets["user_bigdata"]
                        password  = st.secrets["password_bigdata"]
                        host      = st.secrets["host_bigdata"]
                        schema    = 'partyplum'
                        engine    = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
                        df.to_sql('_clientes', engine, if_exists='append', index=False, chunksize=100)
                        engine.dispose()
                        st.session_state.newclient = False
                        st.cache_data.clear()
                        st.rerun()
        st.write('---')

def crearevento(newevent,data):
    IVA = 0.19
    if newevent:
        user      = st.secrets["user_bigdata"]
        password  = st.secrets["password_bigdata"]
        host      = st.secrets["host_bigdata"]
        schema    = 'partyplum'
        engine    = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
        st.write('---')
        data['fecha_registro'] = datetime.now().strftime('%Y-%m-%d')
        link_factura           = None
        
        col1,col2,col3,col4 = st.columns(4)
        with col1:
            fecha_evento = st.date_input('Fecha del evento:')
        with col2:
            ciudad_evento = st.selectbox('Ciudad del evento:', options=['Bogota','Agua de Dios', 'Albán', 'Anapoima', 'Anolaima', 'Apulo', 'Arbeláez', 'Beltrán', 'Bituima', 'Bojacá', 'Cabrera', 'Cachipay', 'Cajicá', 'Caparrapí', 'Cáqueza', 'Carmen de Carupa', 'Chaguaní', 'Chía', 'Chipaque', 'Choachí', 'Chocontá', 'Cogua', 'Cota', 'Cucunubá', 'El Colegio', 'El Peñón', 'El Rosal', 'Facatativá', 'Fómeque', 'Fosca', 'Funza', 'Fúquene', 'Fusagasugá', 'Gachalá', 'Gachancipá', 'Gachetá', 'Gama', 'Girardot', 'Granada', 'Guachetá', 'Guaduas', 'Guasca', 'Guataquí', 'Guatavita', 'Guayabal de Síquima', 'Guayabetal', 'Gutiérrez', 'Jerusalén', 'Junín', 'La Calera', 'La Mesa', 'La Palma', 'La Peña', 'La Vega', 'Lenguazaque', 'Machetá', 'Madrid', 'Manta', 'Medina', 'Mosquera', 'Nariño', 'Nemocón', 'Nilo', 'Nimaima', 'Nocaima', 'Pacho', 'Paime', 'Pandi', 'Paratebueno', 'Pasca', 'Puerto Salgar', 'Pulí', 'Quebradanegra', 'Quetame', 'Quipile', 'Ricaurte', 'San Antonio del Tequendama', 'San Bernardo', 'San Cayetano', 'San Francisco', 'San Juan de Río Seco', 'Sasaima', 'Sesquilé', 'Sibaté', 'Silvania', 'Simijaca', 'Soacha', 'Sopó', 'Subachoque', 'Suesca', 'Supatá', 'Susa', 'Sutatausa', 'Tabio', 'Tausa', 'Tena', 'Tenjo', 'Tibacuy', 'Tibirita', 'Tocaima', 'Tocancipá', 'Topaipí', 'Ubalá', 'Ubaque', 'Une', 'Útica', 'Venecia', 'Vergara', 'Vianí', 'Villagómez', 'Villapinzón', 'Villeta', 'Viotá', 'Yacopí', 'Zipacón', 'Zipaquirá'])
        with col3:
            direccion_evento = st.text_input('Dirección del evento:', value='', max_chars=90)
        with col4:
            paquete = st.selectbox('Paquete:',options=['DECORACION PLUM MINI TABLE','DECORACION PLUM MEDIANO','DECORACION PLUM DELUXE','DECORACION PLUM SPLENDOR','DECORACION PLUM ECOLOGICO'])

        col1,col2,col3,col4 = st.columns(4)
        with col1:
            st.write('')
            st.write('')
            realizado = st.toggle('Evento realizado',value=False)

        with col2:
            uploaded_file  = st.file_uploader("Elige un archivo PDF")
            
        link_factura = None
        with col3:
            if uploaded_file:
                st.write('')
                st.write('')
                if st.button('Subir factura'):
                    link_factura = uploadfileS3('facturas',uploaded_file, f'factura_id_{data["id"].iloc[0]}')
                link_factura = getfileS3('facturas',f'factura_id_{data["id"].iloc[0]}.pdf')
            
        with col4:
            st.write('')
            st.write('')
            valueE = False
            if isinstance(link_factura, str):
                valueE = True
            factura = st.toggle('Factura',value=valueE)

        col1,col2,col3,col4 = st.columns(4)
        with col1:
            valor_factura = st.number_input('Valor Factura:', value=0.0)
        with col2:
            valor_proveedores = st.number_input('Valor Proveedores:', value=0.0)
        with col3:
            ganancia_pp = st.number_input('Ganancia PP:', value=0.0)
        with col4:
            valor = valor_factura-valor_proveedores-ganancia_pp
            ganancia_founder = st.number_input('Ganancia Founder:', value=valor,disabled=True)
            
        col1,col2,col3,col4 = st.columns(4)
        with col1:
            value = ganancia_pp/(1+IVA)
            ganancia_pp_siniva = st.number_input('Ganancia PP sin IVA:', value=value,disabled=True)
        with col2:
            value = ganancia_pp*IVA
            iva_pp = st.number_input('IVA PP:', value=value,disabled=True)
        with col3:
            valor = valor_proveedores+ganancia_founder
            recaudo_terceros = st.number_input('Recaudo Terceros:', value=valor,disabled=True)
        with col4:
            observaciones = st.text_area('Observaciones:', value='')
 
        col1,col2,col3,col4 = st.columns(4)
        with col1:
            st.write('')
            st.write('')
            devolucion = st.toggle('Devolución:', value=0)
        with col2:
            valor_devolucion = None
            if devolucion:
                valor_devolucion = st.number_input('Valor de la Devolución:', value=0.0)
        with col3:
            fecha_devolucion = None
            if devolucion:
                fecha_devolucion = st.date_input('Fecha de Devolución:')


        col1,col2,col3,col4 = st.columns(4)
        with col1:
            valor_total_cuenta_personal = st.number_input('Valor transferencia cuenta personal:', value=0.0)
        with col2:
            tipo_cuenta_personal = st.selectbox('Tipo de la cuenta personal:', options=['','Bancolombia','PNC'])
            tipo_moneda_cuenta_personal = None
            if  tipo_cuenta_personal=='': 
                tipo_cuenta_personal = None
            elif 'Bancolombia' in tipo_cuenta_personal :
                tipo_moneda_cuenta_personal = 'COP'
            elif 'PNC' in tipo_cuenta_personal :
                tipo_moneda_cuenta_personal = 'USD'
        with col3:
            fecha_pago_cuenta_personal = None
            if tipo_cuenta_personal!='':
                fecha_pago_cuenta_personal = st.date_input('Fecha de la transferencia a cuenta personal:')
        with col4:
            tasa_cambio_moneda_cuenta_personal = None
            if 'USD' in tipo_moneda_cuenta_personal :
                tasa_cambio_moneda_cuenta_personal = st.number_input('Tasa de cambio transferencia cuenta personal:', value=0.0)

        data['fecha_evento']       = fecha_evento
        data['ciudad_evento']      = ciudad_evento
        data['direccion_evento']   = direccion_evento
        data['realizado']          = realizado
        data['paquete']            = paquete
        data['factura']            = factura
        data['link_factura']       = link_factura
        data['valor_factura']      = valor_factura
        data['valor_proveedores']  = valor_proveedores
        data['ganancia_founder']   = ganancia_founder
        data['ganancia_pp_siniva'] = ganancia_pp_siniva
        data['iva_pp']             = iva_pp
        data['ganancia_pp']        = ganancia_pp
        data['recaudo_terceros']   = recaudo_terceros
        data['devolucion']         = devolucion
        data['valor_devolucion']   = valor_devolucion
        data['fecha_devolucion']   = fecha_devolucion
        data['observaciones']      = observaciones
        data['valor_total_cuenta_personal']        = valor_total_cuenta_personal
        data['tipo_cuenta_personal']               = tipo_cuenta_personal
        data['tipo_moneda_cuenta_personal']        = tipo_moneda_cuenta_personal
        data['fecha_pago_cuenta_personal']         = fecha_pago_cuenta_personal
        data['tasa_cambio_moneda_cuenta_personal'] = tasa_cambio_moneda_cuenta_personal
        
        col1,col2 = st.columns([0.3,0.7])
        with col1:
            if st.button('Guardar evento'):
                with st.spinner('Guardando evento'):
                    listavar  = list(pd.read_sql_query(f"SELECT * FROM {schema}._facturacion LIMIT 1" , engine))
                    variables = [x for x in listavar if x in data]
                    if 'id' in variables: variables.remove('id')
                    data      = data[variables]
                    data.to_sql('_facturacion', engine, if_exists='append', index=False, chunksize=100)
                    st.session_state.newevent = False
                    st.cache_data.clear()
                    st.rerun()
        engine.dispose()
        st.write('---')

def crearpago(data):
    
    if not data.empty:
        st.write('---')
        col1,col2,col3,col4 = st.columns(4)
        with col1:
            fecha_pago = st.date_input("Fecha de Pago:", datetime.now())
        with col2:
            tipo_pago = st.selectbox("Tipo de Pago:",options=['ANTICIPO','PAGO FINAL'])
        with col3:
            forma_pago = st.selectbox("Forma de Pago:",options=['TRANSFERENCIA','EFECTIVO','CONSIGNACION'])
        with col4:
            valor = st.number_input("Valor", min_value=0.0, format="%.2f")

        comprobante = None
        with col1:
            uploaded_file  = st.file_uploader("Elige un archivo PDF para pagos")
            
        with col2:
            if uploaded_file:
                st.write('')
                st.write('')
                if st.button('Subir comprobante de pago'):
                    comprobante = uploadfileS3('pagos-recibidos',uploaded_file, f'pago_recibido_id_{data["id"].iloc[0]}')
                comprobante = getfileS3('pagos-recibidos',f'pago_recibido_id_{data["id"].iloc[0]}.pdf')
                
        df = pd.DataFrame([{'fecha_pago':fecha_pago,'tipo_pago':tipo_pago,'forma_pago':forma_pago,'valor':valor,'comprobante':comprobante}])
        df['fecha_registro'] = datetime.now().strftime('%Y-%m-%d')
        df['id_facturacion'] = data['id'].iloc[0]
        if valor>0:
            col1,col2 = st.columns([0.3,0.7])
            with col1:
                if st.button('Guardar pago'):
                    with st.spinner('Guardando pago'):
                        user      = st.secrets["user_bigdata"]
                        password  = st.secrets["password_bigdata"]
                        host      = st.secrets["host_bigdata"]
                        schema    = 'partyplum'
                        engine    = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
                        df.to_sql('_pagos_recibidos', engine, if_exists='append', index=False, chunksize=100)
                        engine.dispose()
                        st.session_state.newclient = False
                        st.cache_data.clear()
                        st.rerun()
        st.write('---')

def edit_factura(data,table):
    data = data.dropna(axis=1, how='all')   
    if not data.empty:
        variables = list(data)
        if 'id' in variables: variables.remove('id')
        if 'link' in variables: variables.remove('link')
        if 'fecha_registro' in variables: variables.remove('fecha_registro')
        formatted_string = ', '.join([f'{var}=%s' for var in variables])
        variables.append('id')
        df   = data[variables]
        df   = df.fillna('')
        
        user     = st.secrets["user_bigdata"]
        password = st.secrets["password_bigdata"]
        host     = st.secrets["host_bigdata"]
        schema   = 'partyplum'
        conn = pymysql.connect(host=host,
                       user=user,
                       password=password,
                       db=schema)
        with conn.cursor() as cursor:
            sql = f"UPDATE {schema}.{table} SET {formatted_string} WHERE id=%s"
            list_of_tuples = df.to_records(index=False).tolist()
            cursor.executemany(sql, list_of_tuples)
        conn.commit()
        conn.close() 
        st.cache_data.clear()
        st.rerun()
            
def uploadfileS3(subfolder,file,filename):
    
    ACCESS_KEY  = st.secrets['ACCESS_KEY_digitalocean']
    SECRET_KEY  = st.secrets['SECRET_KEY_digitalocean'] 
    REGION      = st.secrets['REGION_digitalocean']
    BUCKET_NAME = 'partyplum'
    
    session = boto3.session.Session()
    client = session.client('s3', region_name=REGION, endpoint_url=f'https://{REGION}.digitaloceanspaces.com',
                            aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    try:
        fileimport = file.name
        dominio    = fileimport.split('.')[-1]
        filename   = f'{filename}.{dominio}'
        filename   = f'{subfolder}/{filename}'  # Nombre del archivo en el bucket
        file.seek(0) 
        client.upload_fileobj(file, BUCKET_NAME, filename, ExtraArgs={'ACL': 'public-read'})
        url = f'https://{BUCKET_NAME}.{REGION}.digitaloceanspaces.com/{filename}'
        st.success("¡Archivo subido exitosamente!")
    except: 
        url = None
        st.error("Hubo un error al subir el archivo")
    return url

def getfileS3(subfolder,filename):
    
    ACCESS_KEY  = st.secrets['ACCESS_KEY_digitalocean']
    SECRET_KEY  = st.secrets['SECRET_KEY_digitalocean'] 
    REGION      = st.secrets['REGION_digitalocean']
    BUCKET_NAME = 'partyplum'
    
    session = boto3.session.Session()
    client = session.client('s3', region_name=REGION, endpoint_url=f'https://{REGION}.digitaloceanspaces.com',
                            aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    url = None
    try:
        response = client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=f'{subfolder}/{filename}')
        for obj in response.get('Contents', []):
            if filename in obj['Key']:
                url = f'https://{BUCKET_NAME}.{REGION}.digitaloceanspaces.com/{obj["Key"]}'
    except: pass
    return url

if __name__ == "__main__":
    main()