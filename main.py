"""Os métodos para conexão e publicação via MQTT estão desativados,
pois não temos um broker configurado. Tentamos utilizar brokers
gratuitos online, mas não funcionou. """

from machine import Pin, ADC
from dht import DHT22
from time import sleep, localtime
from network import WLAN, STA_IF
from ntptime import settime
# from umqtt.simple import MQTTClient

REDE_WIFI = 'Wokwi-GUEST'
SENHA_WIFI = ''
BROKER_MQTT = 'broker.emqx.io'
ID_CLIENTE_MQTT = 'estufa-joao'
TOPICO_MQTT = b'estufa/ambiente'

PIN_DHT = 14
PIN_LUMINOSIDADE = 34
PIN_LAMPADAS = 26
PIN_VENTILADORES = 27
PIN_IRRIGACAO = 25

sensor_clima = DHT22(Pin(PIN_DHT))
sensor_luminosidade = ADC(Pin(PIN_LUMINOSIDADE))
sensor_luminosidade.atten(ADC.ATTN_11DB)

atuador_lampadas = Pin(PIN_LAMPADAS, Pin.OUT)
atuador_ventiladores = Pin(PIN_VENTILADORES, Pin.OUT)
atuador_agua = Pin(PIN_IRRIGACAO, Pin.OUT)

atuador_lampadas.off()
atuador_ventiladores.off()
atuador_agua.off()

def conectar_rede_wifi():
    print("Estabelecendo conexão com a rede Wi-Fi...")
    interface = WLAN(STA_IF)
    interface.active(True)
    interface.connect(REDE_WIFI, SENHA_WIFI)
    while not interface.isconnected():
        sleep(0.1)
        print(".", end="")
    print(" Conexão estabelecida!")
    print("Endereço IP:", interface.ifconfig()[0])

# def iniciar_mqtt():
#     print("Conectando ao servidor MQTT...")
#     cliente = MQTTClient(ID_CLIENTE_MQTT, BROKER_MQTT)
#     cliente.connect()
#     print("Conexão MQTT realizada com sucesso!")
#     return cliente

def ajustar_horario():
    settime()

# def enviar_dados_mqtt(cliente, temperatura, umidade, valor_ldr, estado_lamp, estado_vent, estado_agua):
#     mensagem = (
#         '{"temperatura": ' + str(temperatura) +
#         ', "umidade": ' + str(umidade) +
#         ', "luminosidade": ' + str(valor_ldr) +
#         ', "lampadas": ' + str(estado_lamp) +
#         ', "ventiladores": ' + str(estado_vent) +
#         ', "agua": ' + str(estado_agua) + '}'
#     )
#     cliente.publish(TOPICO_MQTT, mensagem)

def gerenciar_ambiente(temp, umidade, horario, irrigacao_agendada):
    if temp < 18:
        atuador_lampadas.on()
        atuador_ventiladores.off()
    elif temp > 22:
        atuador_lampadas.off()
        atuador_ventiladores.on()
    else:
        atuador_lampadas.off()
        atuador_ventiladores.off()

    if horario[3] == 17 and horario[4] == 0 and not irrigacao_agendada:
        print("Irrigação programada às 17h")
        atuador_agua.on()
        return True

    if umidade < 60:
        if not atuador_agua.value():
            print("Umidade baixa - iniciando irrigação.")
            print("-" * 20)
            atuador_agua.on()
    else:
        if atuador_agua.value():
            print("Umidade normalizada - desligando irrigação.")
            print("-" * 20)
            atuador_agua.off()

    return irrigacao_agendada

def executar_loop():
    conectar_rede_wifi()
    ajustar_horario()
    # cliente_mqtt = iniciar_mqtt()

    irrigacao_agendada = False
    data_atual = None

    while True:
        try:
            sensor_clima.measure()
            temp = sensor_clima.temperature()
            umidade = sensor_clima.humidity()
            luz = sensor_luminosidade.read()

            print("Temperatura:", temp)
            print("Umidade:", umidade)
            print("Luminosidade:", luz)
            print("Lâmpadas:", "ATIVADAS" if atuador_lampadas.value() else "DESATIVADAS")
            print("Ventiladores:", "ATIVADOS" if atuador_ventiladores.value() else "DESATIVADOS")
            print("Água:", "ATIVADA" if atuador_agua.value() else "DESATIVADA")
            print("-" * 20)

            horario_atual = localtime()
            if data_atual != horario_atual[2]:
                data_atual = horario_atual[2]
                irrigacao_agendada = False

            irrigacao_agendada = gerenciar_ambiente(temp, umidade, horario_atual, irrigacao_agendada)

            # enviar_dados_mqtt(
            #     cliente_mqtt,
            #     temp,
            #     umidade,
            #     luz,
            #     int(atuador_lampadas.value()),
            #     int(atuador_ventiladores.value()),
            #     int(atuador_agua.value())
            # )

            sleep(6)

        except Exception as erro:
            print("Erro detectado:", erro)
            sleep(10)

executar_loop()
