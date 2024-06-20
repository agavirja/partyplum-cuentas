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
        dataproveedores = getproveedores()
    
    col1, col2 = st.columns(2)
    with col1:
        options   = list(dataproveedores[dataproveedores['nombre'].notnull()]['nombre'].unique())+list(dataproveedores[dataproveedores['razonsocial'].notnull()]['razonsocial'].unique())
        options   = ['']+list(sorted(options))
        proveedor = st.selectbox('Seleccionar proveedor:',options=options)
    
    #-------------------------------------------------------------------------#
    # Proveedores
    if proveedor=='':
        titulo = 'Crear nuevo proveedor'
        html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Título Centrado</title></head><body><section style="text-align: center;"><h1 style="color: #fff; font-size: 20px; font-family: Arial, sans-serif; font-weight: bold; background-color: #9D57BA; padding: 10px;">{titulo}</h1></section></body></html>"""
        texto = BeautifulSoup(html, 'html.parser')
        st.markdown(str(texto), unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            #newproveedor = st.toggle('Crear nuevo proveedor',value=False)
            newproveedor = st.checkbox('Crear nuevo proveedor',value=False)

        registrarproveedor(newproveedor)
        
    #-------------------------------------------------------------------------#
    # Proveedores
    if proveedor!='':
        titulo = 'Crear pago para el proveedor'
        html   = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Título Centrado</title></head><body><section style="text-align: center;"><h1 style="color: #fff; font-size: 20px; font-family: Arial, sans-serif; font-weight: bold; background-color: #9D57BA; padding: 10px;">{titulo}</h1></section></body></html>"""
        texto  = BeautifulSoup(html, 'html.parser')
        st.markdown(str(texto), unsafe_allow_html=True)
        df = dataproveedores[(dataproveedores['nombre']==proveedor) | (dataproveedores['razonsocial']==proveedor)].iloc[[0]]
        crearpago(df)
        
    #-------------------------------------------------------------------------#
    # Pagos
    
    with st.spinner('Datos de pago al proveedor'):
        datapagoproveedores = getpagosproveedores(proveedor)
    
    height=200
    titulo = 'Información de pago al proveedor'
    if proveedor=='': 
        height=500
        titulo = 'Información de pagos a proveedores'

    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Título Centrado</title></head><body><section style="text-align: center;"><h1 style="color: #fff; font-size: 20px; font-family: Arial, sans-serif; font-weight: bold; background-color: #9D57BA; padding: 10px;">{titulo}</h1></section></body></html>"""
    texto = BeautifulSoup(html, 'html.parser')
    st.markdown(str(texto), unsafe_allow_html=True)
    st.write('')
    st.write('')
    
    df        = datapagoproveedores.copy()
    variables = ['id','fecha_pago','valor_pago', 'pagada', 'concepto','tipopago','formapago', 'iva','retenciones','link_factura_cuenta', 'link_comprobante_pago']
    variables = [x for x in variables if x in df]
    df        = df[variables]
    df.rename(columns={'link_factura_cuenta':'link factura','link_comprobante_pago':'link pago'},inplace=True)
    gb = GridOptionsBuilder.from_dataframe(df,editable=True)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    cell_renderer =  JsCode("""function(params) {return `<a href=${params.value} target="_blank">${params.value}</a>`}""")
    
    gb.configure_column(
        "link factura",
        headerName="link factura",
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
                height=height)
    col1,col2 = st.columns([0.3,0.7])
    with col1:
        if st.button('Guardar'):
            with st.spinner('Guardando pagos proveedores'):
                edit_pago_proveedores(response['data'],'_pagos_proveedores')

@st.cache_data(show_spinner=False)
def getproveedores():
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata"]
    schema   = 'partyplum'
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    data     = pd.read_sql_query("SELECT * FROM partyplum._proveedores" , engine)
    engine.dispose()
    return data

@st.cache_data(show_spinner=False)
def getpagosproveedores(proveedor=None):
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata"]
    schema   = 'partyplum'
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    query    = ""
    if isinstance(proveedor, str) and proveedor!='':
        query = f"WHERE nombre='{proveedor}' or razonsocial='{proveedor}'"
    data = pd.read_sql_query(f"SELECT * FROM partyplum._pagos_proveedores {query}" , engine)
    if not data.empty:
        data = data.sort_values(by='fecha_pago',ascending=False)
    engine.dispose()
    return data
def registrarproveedor(newproveedor):
    if newproveedor:
        st.write('---')
        col1,col2,col3,col4 = st.columns(4)
        razonsocial = None
        with col1:
            tipoproveedor = st.selectbox('Tipo del cliente:',options=['Natural','Juridica'])
        if 'Natural' in tipoproveedor:
            with col2:
                tipo_identificacion = st.selectbox('Tipo de documento:',options=['CC','CE'])
        elif 'Juridica' in tipoproveedor:
            with col2:
                tipo_identificacion = st.selectbox('Tipo de documento:',options=['NIT'])
            with col4:
                razonsocial = st.text_input('Razón social:',value='').upper().strip()
        with col3:
            identificacion = st.text_input('Identificación:',value='')
        with col4:
            nombre_proveedor = st.text_input('Nombre del cliente:',value='').upper().strip()
        with col1:
            telefono = st.text_input('Teléfono:',value='')
        with col2:
            email = st.text_input('Email:',value='')
        
        df = pd.DataFrame([{'tipoproveedor':tipoproveedor,'tipo_identificacion':tipo_identificacion,'razonsocial':razonsocial,'identificacion':identificacion,'nombre':nombre_proveedor,'telefono':telefono,'email':email}])
        df['fecha_registro'] = datetime.now().strftime('%Y-%m-%d')
        df['available']      = 1
        if nombre_proveedor!='' and tipo_identificacion!='' and identificacion!='':
            col1,col2 = st.columns([0.3,0.7])
            with col1:
                if st.button('Guardar proveedor'):
                    with st.spinner('Guardando proveedor'):
                        user      = st.secrets["user_bigdata"]
                        password  = st.secrets["password_bigdata"]
                        host      = st.secrets["host_bigdata"]
                        schema    = 'partyplum'
                        engine    = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
                        df.to_sql('_proveedores', engine, if_exists='append', index=False, chunksize=100)
                        engine.dispose()
                        st.session_state.newproveedor = False
                        st.cache_data.clear()
                        st.rerun()
        st.write('---')
        
        
def crearpago(data):
    
    if not data.empty:
        st.write('---')
        col1,col2,col3,col4 = st.columns(4)
        with col1:
            fecha_pago = st.date_input("Fecha de Pago:", datetime.now())
        with col2:
            tipopago = st.selectbox("Tipo de Pago:",options=['RECAUDO A TERCEROS','OTROS PAGOS'])
        with col3:
            formapago = st.selectbox("Forma de Pago:",options=['TRANSFERENCIA','EFECTIVO','CONSIGNACION'])
        with col4:
            valor_pago = st.number_input("Valor:", min_value=0.0, format="%.2f")

        col1,col2,col3,col4 = st.columns(4)
        with col1:
            iva = st.number_input("IVA:",min_value=0.0, format="%.2f")
        with col2:
            retenciones = st.number_input("Retenciones:",min_value=0.0, format="%.2f")
        with col3:
            st.write('')
            st.write('')
            #pagada = st.toggle("Pagada",value=False)
            pagada = st.checkbox("Pagada",value=False)
        with col4:
            concepto = st.text_area("Concepto del pago:",value='')
            
        #---------------------------------------------------------------------#
        # Link comprobante de pago
        col1,col2,col3,col4 = st.columns(4)
        link_comprobante_pago = None
        with col1:
            uploaded_file  = st.file_uploader("Subir el comprobante de pago")
            
        with col2:
            if uploaded_file:
                st.write('')
                st.write('')
                if st.button('Subir comprobante de pago '):
                    link_comprobante_pago = uploadfileS3('pagos-proveedores',uploaded_file, f'pago_proveedores_id_{data["id"].iloc[0]}')
                link_comprobante_pago = getfileS3('pagos-proveedores',f'pago_proveedores_id_{data["id"].iloc[0]}.pdf')

        #---------------------------------------------------------------------#
        # Link factura o cuenta
        col1,col2,col3,col4 = st.columns(4)
        link_factura_cuenta = None
        with col1:
            uploaded_file  = st.file_uploader("Subir la factura o cuenta de cobro")
            
        with col2:
            if uploaded_file:
                st.write('')
                st.write('')
                if st.button('Subir la factura o cuenta de cobro '):
                    link_factura_cuenta = uploadfileS3('cuenta-cobro-proveedores',uploaded_file, f'cuenta_proveedores_id_{data["id"].iloc[0]}')
                link_factura_cuenta = getfileS3('cuenta-cobro-proveedores',f'cuenta_proveedores_id_{data["id"].iloc[0]}.pdf')
                 
        data['fecha_pago']            = fecha_pago
        data['tipopago']              = tipopago
        data['formapago']             =  formapago
        data['valor_pago']            =  valor_pago
        data['pagada']                = pagada
        data['concepto']              = concepto
        data['iva']                   = iva
        data['retenciones']           = retenciones
        data['link_comprobante_pago'] = link_comprobante_pago
        data['link_factura_cuenta']   = link_factura_cuenta
        data['fecha_registro']        = datetime.now().strftime('%Y-%m-%d')
        col1,col2 = st.columns([0.3,0.7])
        with col1:
            if st.button('Guardar pago'):
                with st.spinner('Guardando pago'):
                    user      = st.secrets["user_bigdata"]
                    password  = st.secrets["password_bigdata"]
                    host      = st.secrets["host_bigdata"]
                    schema    = 'partyplum'
                    engine    = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
                    listavar  = list(pd.read_sql_query(f"SELECT * FROM {schema}._pagos_proveedores LIMIT 1" , engine))
                    variables = [x for x in listavar if x in data]
                    data      = data[variables]
                    data.to_sql('_pagos_proveedores', engine, if_exists='append', index=False, chunksize=100)
                    engine.dispose()
                    st.session_state.newclient = False
                    st.cache_data.clear()
                    st.rerun()
        st.write('---')
        
def edit_pago_proveedores(data,table):
    data = data.dropna(axis=1, how='all')   
    if not data.empty:
        variables = list(data)
        if 'id' in variables: variables.remove('id')
        if 'fecha_registro' in variables: variables.remove('fecha_registro')
        variablesdata = ['fecha_pago', 'valor_pago', 'pagada', 'concepto', 'tipopago', 'formapago', 'iva', 'retenciones', 'link_factura_cuenta', 'link_comprobante_pago']
        variables     = [x for x in variablesdata if x in list(data)]

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