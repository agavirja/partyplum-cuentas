import streamlit as st
import pandas as pd
import calendar
import plotly.express as px
from sqlalchemy import create_engine
from bs4 import BeautifulSoup


from display.style_white import style 

st.set_page_config(layout='wide')

def main():

    titulo = 'Descargar cuentas'
    html   = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Título Centrado</title></head><body><section style="text-align: center;"><h1 style="color: #fff; font-size: 20px; font-family: Arial, sans-serif; font-weight: bold; background-color: #9D57BA; padding: 10px;">{titulo}</h1></section></body></html>"""
    texto = BeautifulSoup(html, 'html.parser')
    st.markdown(str(texto), unsafe_allow_html=True)
    
    style()
        
    st.write('')
    st.write('')
    st.write('')
        
    with st.spinner('Cargando información'):
        datafacturacion = getcuentas()
            
    col1,col2,col3 = st.columns([0.4,0.4,0.2])
    with col1:
        options = [2024]
        year    = st.selectbox('Año del evento: ',options=options)
        
    with col2:
        options   = ['Todos','Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
        seleccion = st.selectbox('Cuentas para eventos del mes de: ',options=options)
    
    if 'todo' not in seleccion.lower():
        datafacturacion = datafacturacion[datafacturacion['MES DE EVENTO']==seleccion]
        
    with col3:
        st.write('')
        st.write('')
        if st.button('Descargar Excel'):
            download_excel(datafacturacion)
    
    html = reporteHtml(datafacturacion=datafacturacion)
    st.components.v1.html(html, height=550)

    
    col1,col2 = st.columns(2)
    with col1:
        titulo = 'Clientes'
        html   = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Título Centrado</title></head><body><section style="text-align: center;"><h1 style="color: #fff; font-size: 20px; font-family: Arial, sans-serif; font-weight: bold; background-color: #9D57BA; padding: 10px;">{titulo}</h1></section></body></html>"""
        texto = BeautifulSoup(html, 'html.parser')
        st.markdown(str(texto), unsafe_allow_html=True)
        st.write('')
        datacliente       = datafacturacion[['MES DE EVENTO','CLIENTE','FECHA EVENTO','VALOR DEL PAGO']].sort_values(by=['FECHA EVENTO','CLIENTE'],ascending=True)
        datacliente.index = range(len(datacliente))
        st.dataframe(datacliente)
    
    with col2:
        titulo = 'Falta por facturar'
        html   = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Título Centrado</title></head><body><section style="text-align: center;"><h1 style="color: #fff; font-size: 20px; font-family: Arial, sans-serif; font-weight: bold; background-color: #9D57BA; padding: 10px;">{titulo}</h1></section></body></html>"""
        texto = BeautifulSoup(html, 'html.parser')
        st.markdown(str(texto), unsafe_allow_html=True)

        datacliente = datafacturacion[['MES DE EVENTO','CLIENTE','FECHA EVENTO','FACTURA']].sort_values(by=['FECHA EVENTO','CLIENTE'],ascending=True)
        datacliente = datacliente[datacliente['FACTURA']!=1]
        if not datacliente.empty:
            st.write('')
            datacliente.index = range(len(datacliente))
            st.dataframe(datacliente[['MES DE EVENTO','CLIENTE','FECHA EVENTO']])
        
@st.cache_data(show_spinner=False)
def getcuentas():
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata"]
    schema   = 'partyplum'
    
    engine          = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    datafacturacion = pd.read_sql_query("SELECT * FROM partyplum._facturacion;" , engine)
    datapagos       = pd.read_sql_query("SELECT * FROM partyplum._pagos_recibidos;" , engine)
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
    
    return datafacturacion

def download_excel(df):
    excel_file = df.to_excel('cuentas_party_plum.xlsx', index=False)
    with open('cuentas_party_plum.xlsx', 'rb') as f:
        data = f.read()
    st.download_button(
        label="Haz clic aquí para descargar",
        data=data,
        file_name='cuentas_party_plum.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    

@st.cache_data(show_spinner=False)
def reporteHtml(datafacturacion):
    
    html_header = ""
    if not datafacturacion.empty:
        formato = [{'texto':'Ganancia Vivi','value':datafacturacion['GANANCIA VIVI'].sum()},
                   {'texto':'Ganancia Party Plum (sin IVA)','value':datafacturacion['GANANCIA PARTY PLUM SIN IVA'].sum()},
                   {'texto':'Pago Proveedores','value':datafacturacion['PROVEEDORES'].sum()},
                   ]
        html_paso = ""
        for i in formato:
            if i['value'] is not None:
                value      = '{:,.0f}'.format(i['value'])
                html_paso += f"""
                <div class="col-4 col-md-4 mb-3">
                    <div class="card card-stats card-round">
                        <div class="card-body">
                            <div class="row align-items-center">
                                <div class="col col-stats ms-3 ms-sm-0">
                                    <div class="numbers">
                                        <h4 class="card-title">{value}</h4>
                                        <p class="card-category">{i['texto']}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                """
        if html_paso!="":
            html_header = f"""
            <div class="row">
                {html_paso}
            </div>
            """

    #-------------------------------------------------------------------------#
    # Eventos
    html_agregado = ""
    if not datafacturacion.empty:
        html_grafica = ""
        df = datafacturacion.copy()
       
        df         = df.groupby('MES DE EVENTO').agg({'EVENTO REALIZADO':'sum'}).reset_index()
        df.columns = ['fecha','value']
        df.index   = range(len(df))
        
        meses_orden = {'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6,'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12}
        df['mes_orden'] = df['fecha'].map(meses_orden)
        
        df = df.sort_values(by='mes_orden')
        
        if not df.empty:
            fig = px.bar(df, x='fecha', y='value', title='Eventos Realizados por Mes',color_discrete_sequence=['#636EFA'])

            fig.update_layout(
                title="",
                xaxis_title=None,
                yaxis_title=None,

                #height=200, 
                height=200,
                plot_bgcolor='rgba(0, 0, 0, 0)',
                paper_bgcolor='rgba(0, 0, 0, 0)',
                margin=dict(l=0, r=0, t=0, b=20),
            )

            fig.update_xaxes(tickmode='linear', dtick=1, tickfont=dict(color='black'),showgrid=False, zeroline=False,)
            fig.update_yaxes(showgrid=False, zeroline=False, tickfont=dict(color='black'), title_font=dict(color='black'))
            fig.update_yaxes(title=None, secondary_y=True, showgrid=False, zeroline=False, tickfont=dict(color='black'))
            html_fig_paso = fig.to_html(config={'displayModeBar': False})
            try:
                soup = BeautifulSoup(html_fig_paso, 'html.parser')
                soup = soup.find('body')
                soup = str(soup.prettify())
                soup = soup.replace('<body>', '<div style="margin-bottom: 0px;">').replace('</body>', '</div>')
                html_grafica = f""" 
                <div class="col-8">
                    <div class="card card-stats card-round card-custom">
                        <div class="card-body card-body-custom">
                            <div class="row align-items-center">
                                <div class="col col-stats ms-3 ms-sm-0">
                                    <div class="graph-container" style="width: 100%; height: auto;">
                                        {soup}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                """
            except: pass
        
        html_inputs = ""
        if not datafacturacion.empty:
            input1   = '{:,.0f}'.format(int(len(datafacturacion)))
            input2   = '{:,.0f}'.format(int(len(datafacturacion['CLIENTE'].unique())))
            html_inputs = f"""
            <div class="col-4">
                <div class="row mb-3">
                    <div class="col-12 mb-3">
                        <div class="card card-stats card-round">
                            <div class="card-body">
                                <div class="row align-items-center">
                                    <div class="col col-stats ms-3 ms-sm-0">
                                        <div class="numbers">
                                            <h4 class="card-title" style="margin-bottom: 10px;">{input1}</h4>
                                            <p class="card-category">Eventos</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-12">
                        <div class="card card-stats card-round">
                            <div class="card-body">
                                <div class="row align-items-center">
                                    <div class="col col-stats ms-3 ms-sm-0">
                                        <div class="numbers">
                                            <h4 class="card-title" style="margin-bottom: 10px;">{input2}</h4>
                                            <p class="card-category">Clientes únicos</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
        html_agregado = f"""
        <div class="row">
            {html_inputs}
            {html_grafica}
        </div>
        """
        
        
    #-------------------------------------------------------------------------#
    # Valor
    html_valor = ""
    if not datafacturacion.empty:
        html_grafica = ""
        df = datafacturacion.copy()
       
        df         = df.groupby('MES DE EVENTO').agg({'VALOR DEL PAGO':'sum'}).reset_index()
        df.columns = ['fecha','value']
        df.index   = range(len(df))
        
        meses_orden = {'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6,'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12}
        df['mes_orden'] = df['fecha'].map(meses_orden)
        
        df = df.sort_values(by='mes_orden')
        
        if not df.empty:
            fig = px.bar(df, x='fecha', y='value', title='Eventos Realizados por Mes',color_discrete_sequence=['#636EFA'])

            fig.update_layout(
                title="",
                xaxis_title=None,
                yaxis_title=None,

                #height=200, 
                height=200,
                plot_bgcolor='rgba(0, 0, 0, 0)',
                paper_bgcolor='rgba(0, 0, 0, 0)',
                margin=dict(l=0, r=0, t=0, b=20),
            )

            fig.update_xaxes(tickmode='linear', dtick=1, tickfont=dict(color='black'),showgrid=False, zeroline=False,)
            fig.update_yaxes(showgrid=False, zeroline=False, tickfont=dict(color='black'), title_font=dict(color='black'))
            fig.update_yaxes(title=None, secondary_y=True, showgrid=False, zeroline=False, tickfont=dict(color='black'))
            html_fig_paso = fig.to_html(config={'displayModeBar': False})
            try:
                soup = BeautifulSoup(html_fig_paso, 'html.parser')
                soup = soup.find('body')
                soup = str(soup.prettify())
                soup = soup.replace('<body>', '<div style="margin-bottom: 0px;">').replace('</body>', '</div>')
                html_grafica = f""" 
                <div class="col-8">
                    <div class="card card-stats card-round card-custom">
                        <div class="card-body card-body-custom">
                            <div class="row align-items-center">
                                <div class="col col-stats ms-3 ms-sm-0">
                                    <div class="graph-container" style="width: 100%; height: auto;">
                                        {soup}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                """
            except: pass
        
        html_inputs = ""
        if not datafacturacion.empty:
            valortoal = int(datafacturacion['VALOR DEL PAGO'].sum() // 1000 * 1000)
            input1    = f"${valortoal:,.0f}"
            valortoal = int(datafacturacion['VALOR DEL PAGO'].median() // 1000 * 1000)
            input2    = f"${valortoal:,.0f}"
            html_inputs = f"""
            <div class="col-4">
                <div class="row mb-3">
                    <div class="col-12 mb-3">
                        <div class="card card-stats card-round">
                            <div class="card-body">
                                <div class="row align-items-center">
                                    <div class="col col-stats ms-3 ms-sm-0">
                                        <div class="numbers">
                                            <h4 class="card-title" style="margin-bottom: 10px;">{input1}</h4>
                                            <p class="card-category">Recaudo total</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-12">
                        <div class="card card-stats card-round">
                            <div class="card-body">
                                <div class="row align-items-center">
                                    <div class="col col-stats ms-3 ms-sm-0">
                                        <div class="numbers">
                                            <h4 class="card-title" style="margin-bottom: 10px;">{input2}</h4>
                                            <p class="card-category">Valor promedio evento</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
        html_valor = f"""
        <div class="row">
            {html_inputs}
            {html_grafica}
        </div>
        """
        
    style = """
    <style>
        body, html {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        .card {
            --bs-card-spacer-y: 1rem;
            --bs-card-spacer-x: 1rem;
            --bs-card-title-spacer-y: 0.5rem;
            --bs-card-title-color: #000;
            --bs-card-subtitle-color: #6c757d;
            --bs-card-border-width: 1px;
            --bs-card-border-color: rgba(0, 0, 0, 0.125);
            --bs-card-border-radius: 0.25rem;
            --bs-card-box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            --bs-card-inner-border-radius: calc(0.25rem - 1px);
            --bs-card-cap-padding-y: 0.5rem;
            --bs-card-cap-padding-x: 1rem;
            --bs-card-cap-bg: rgba(0, 123, 255, 0.03);
            --bs-card-cap-color: #007bff;
            --bs-card-height: auto;
            --bs-card-color: #000;
            --bs-card-bg: #fff;
            --bs-card-img-overlay-padding: 1rem;
            --bs-card-group-margin: 0.75rem;
            position: relative;
            display: flex;
            flex-direction: column;
            min-width: 0;
            height: var(--bs-card-height);
            color: var(--bs-card-color);
            word-wrap: break-word;
            background-color: var(--bs-card-bg);
            background-clip: border-box;
            border: var(--bs-card-border-width) solid var(--bs-card-border-color);
            border-radius: var(--bs-card-border-radius);
            box-shadow: var(--bs-card-box-shadow);
        }

        .card-stats .icon-big {
            font-size: 3rem;
            line-height: 1;
            color: #fff;
        }

        .card-stats .icon-primary {
            background-color: #007bff;
        }

        .bubble-shadow-small {
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            border-radius: 50%;
            padding: 1rem;
        }

        .card-stats .numbers {
            font-size: 2rem;
            font-weight: bold;
            text-align: center;
        }

        .card-stats .card-category {
            color: #6c757d;
            font-size: 0.8rem;
            margin: 0;
            text-align: center;
        }

        .card-stats .card-title {
            margin: 0;
            font-size: 1.2rem;
            font-weight: bold;
            text-align: center;
        }
        
        .small-text {
            font-size: 0.3rem; 
            color: #6c757d; 
        }
        .graph-container {
            width: 100%;
            height: 100%;
            margin-bottom: 0;
        }
        
        .card-custom {
            height: 215px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }

        .card-body-custom {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
        }
    </style>
    """
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Visitors Card</title>
        <!-- Incluyendo Bootstrap CSS para el diseño de las tarjetas -->
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/5.0.0-alpha1/css/bootstrap.min.css">
        <!-- Font Awesome para los íconos -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        {style}
    </head>
    <body>
        <div class="container-fluid">
            {html_header}
            {html_agregado}
            {html_valor}
        </div>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    main()
    