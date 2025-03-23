#!/usr/bin/python3
import argparse
import sys
import signal
import numpy as np
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description='Simulate flow from solar thermal collector')
parser.add_argument('-p','--plot', action='store_true', help='Plot thermal simulation for specific pump runtime')
parser.add_argument('-t','--pump_runtime', type=float, default=160, help='Pump runtime for specific simulation, or start point for optimization')
args = parser.parse_args()
# example usage find optimum: ./soltherm.py
# example usage plot:         ./soltherm.py -p -t 170
# ToDo: Rohr ist ab Solarstation zum Speicher dicker (in Solarstation und danach 22mm Außendurchmesser; zum Dach 15mm)
# ToDo: Bei Befüllung den Soleinhalt notieren zur Modellverifikation.
# ToDo: Bei wenig Durchfluss evtl. keine turbulente Strömung im Kollektor und damit schlechterer Wärmeübergang?

# Viessmann DuoSol H30 Röhren
#
# Viessmann CeraCell-bivalent 300Liter-Speicher Aufbau:
#
# 127cm Höhe(Orangene Verkleidung)
# 120cm Wasser hot
# 103cm Heizung Vorlauf
#  90cm ZirkLeitung; TempSensor Heizung
#  77cm Heizung Rücklauf
#  70cm Solar Vorlauf
#  51cm TempSensor Solar
#  20cm Solar Rücklauf
#   4cm Wasser cold
#   0cm Beginn(Orangene Verkleidung)
#
#
# Kollektor -> Rohr -> Solarstation -> Eigener VL-Sensor -> 48cm Rohr -> SpeicherEintritt -> SpeicherAustritt -> 64cm Rohr -> Eigener RL-Sensor ->
L_VLsens_Sp = 0.48

kill = 0

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    kill = 1
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

rho_cu = 8960  # Dichte von Kupfer in kg/m³
c_cu = 385  # spezifische Wärmekapazität Kupfer in J/(kg*K)
lambda_cu = 380  # Wärmeleitfähigkeit von Kupfer W/(mK)
#d_iso = 0.013  # Dämmstärke in m
#m_iso = 0.112  # spezifische Masse der Dämmung in kg/m
#c_iso = 800  # spezifische Wärmekapazität Dämmung in J/(kg*K)
#lambda_iso = 0.042  # Wärmeleitfähigkeit der Dämmung bei 40°C (Kaimann, 2017) in W/(mK)

########################################
# Fluid: Tyfocor LS Kälteschutz -28 °C #
########################################
# Quelle: Datenblatt Tyfocor LS
rho_fluid = 1015  # Dichte der Sole bei 50°C in kg/m³
#visc_fluid = 4.95e-6  # Kinematische Viskosität (20 °C) in m²/s
visc_fluid = 1.91e-6  # Kinematische Viskosität (50 °C) in m²/s
#visc_fluid = 1.08e-6  # Kinematische Viskosität (80 °C) in m²/s
#visc_water = 1.002e-6  # Kinematische Viskosität (20 °C) in m²/s
c_fluid = 3720  # spezifische Wärmekapazität der Sole bei 50°C in J/(kg*K)
#c_water = 4180  # spezifische Wärmekapazität von Wasser in J/(kg*K)

# Bei 4l/min und Tdelta von 6K werden 1466 Watt transportiert

#################
# Dachkollektor #
#################
q_flux = 700  # Einstrahlung in W/m²
area = 3  # Kollektorfläche in m²
eff = 0.8  # Wirkungsgrad
P_col = eff*q_flux*area  # Kollektorleistung in W
print('Kollektorleistung: {:.0f} W'.format(P_col))
# Annahme für Wärmetauscher: Rechteckiger Querschnitt 5cm Breit und 2cm hoch 3mm Kupferdicke ->
b_col = 0.05
d_col = 0.003
h_col = 0.02
Ai_col = (h_col-2*d_col) * (b_col-2*d_col)
Aa_col = b_col*h_col - Ai_col
#Da_col = 0.045  # Außendurchmesser in m
#Di_col = 0.04  # Innendurchmesser in m
L_col = 2*2.16*1.1  # Rohrlänge in m 1.1 da gewellt
print('Kollektorinhalt: {:.1f} l'.format( 1000*L_col*Ai_col))
#T_outdoor = 10  # Umgebungslufttemperatur in °C


##############
# Rohrsystem #
##############
Da = 0.015  # Außendurchmesser in m
Di = 0.013  # Innendurchmesser in m

#c_pipe = (Da**2-Di**2)*np.pi/4*rho_Cu*c_Cu + m_iso*c_iso  # Wärmekapazität gedämmtes Rohr in J/(kg*K)
#print(c_pipe)
#U_pipe_loss = 0.271  #  Wärmeverlust pro Meter Rohrleitung W/(m*K)

###########
# Vorlauf #
###########
#L_vor = 13.5  # m geschätzt
L_vor = (0.48+0.2+1.2+0.09+0.14+
# 14cm=Kellerwand
1.54+(1.43+1.92+1.39)+0.13+0.31+
# 31cm=Kellerdecke
2.68+0.17+
# 17cm=Decke
2.4+0.28+
# 28cm=Decke
0.36+2.8+0.49+1.334)
# (66cm bis Holzplatte); 6Ziegelx29,9cm - 46cm(bis Leitungsknick bis Schrägbalken) = 133.4cm

############
# Rücklauf #
############
#L_rück = 13.5  # m geschätzt
L_rück = (0.6+0.06+1.92+0.09+0.14+
# 14cm=Kellerwand
1.64+(1.26+1.88+1.32)+0.11+0.31+
# 31cm=Kellerdecke
2.68+0.17+
# 17cm=Decke
2.4+0.28+
# 28cm=Decke
0.3+2.98+0.48+1.234)
# (56cm bis Holzplatte); 6Ziegelx29,9cm - 56cm(bis Leitungsknick bis Schrägbalken) = 123.4cm

print('Soleinhalt: VL: {:.1f} l  RL: {:.1f} l'.format( 1000*L_vor*np.pi*((Di/2)**2), 1000*L_rück*np.pi*((Di/2)**2) ))
print('L_vor={:.3f} m  L_rück={:.3f} m'.format(L_vor, L_rück))


#################
# Wärmetauscher #
#################
# Inhalt CeraCell-bivalent: 9.5 Liter
# Dauerleistung 10°C auf 45°C mit 70°C Heizwasser: 33kW
Da_WT = 0.038  # Außendurchmesser Wärmetauscherrohr in m
Di_WT = 0.035  # Innendurchmesser Wärmetauscherrohr in m
V_WT = 9.5  # Heizwendelinhalt in Liter
L_WT = V_WT/1000 / (np.pi*(Di_WT/2)**2)  # Länge der Heizwendel in m
print('Heizwendel/Wärmetauscher im Speicher: Länge: {:.2f} m  Inhalt: {:.2f} l'.format(L_WT, V_WT))

#V_sp = 0.3  # Speicherinhalt in m³


#########
# Pumpe #
#########
#Reynoldszahl < 2000 -> laminare Strömung
#Reynoldszahl 2000-4000 -> laminare Strömung aufgrund von Turbulenzen instabil
#Reynoldszahl > 4000 -> turbulenten Strömung
#Quelle2: Rekrit = 2200 bis 2300

P_pump = 45  # Leistung in Watt bei Stufe 1 4l/min -> Reynoldszahl im Rohr: 3419
#P_pump = 65  # Leistung in Watt bei Stufe 2 6l/min -> Reynoldszahl im Rohr: 5128
#P_pump = 90  # Leistung in Watt bei Stufe 3 7l/min -> Reynoldszahl im Rohr: 5982
Vd = 4  # Durchfluss in l/min

m = rho_fluid * Vd/1000 /60  # Massenstrom in kg/s
print('Massenstrom: {:.1f} l/min = {:.3f} kg/s'.format(Vd, m))
print('Geschwindigkeit im Kollektor: {:.3f} m/s'.format(m/(rho_fluid*Ai_col)))
v_rohr = m/(rho_fluid*np.pi*(Di/2)**2)  # mittlere Strömungsgeschwindigkeit [m/s]
print('Geschwindigkeit im Rohr:      {:.3f} m/s'.format(v_rohr))
print('Geschwindigkeit im Speicher:  {:.3f} m/s'.format(m/(rho_fluid*np.pi*(Di_WT/2)**2)))

Reynoldszahl = v_rohr*Di/visc_fluid
print('Reynoldszahl im Rohr: {:.0f}'.format(Reynoldszahl))


#T_Rohr_Mess_Eintritt  # Temperatur Rohrleitungseintritt
#T_Rohr_Mess_Austritt Temperatur Rohrleitungsaustritt


# Simulation
dt = 0.2   #s, time step
nodes_distance = .2
N_col = int(L_col/nodes_distance)  # simulation nodes im Kollektor
N_v = int(L_vor/nodes_distance)    # simulation nodes im Vorlauf
N_r = int(L_rück/nodes_distance)   # simulation nodes im Rücklauf
N_WT = int(L_WT/nodes_distance)    # simulation nodes im Speicher Wärmetauscher
N = N_col + N_v + N_r + N_WT
print('Simulation nodes:', N)

L_sys = L_col+L_vor+L_rück+L_WT
dx = L_sys/N  #m Knotenabstand

#Ti = 20  # °C pipe inlet temperature
T0_col = 79  # Initiale Kollektortemperatur in °C
T0_vor = 26  # Initiale Vorlauftemperatur in °C
T0_rück = 25  # Initiale Rücklauftemperatur in °C
T0_sp = T0_col-39  # Initiale Speichertemperatur in °C

# Optimale Pumpelaufzeit für maximale Energie
# mit 700W/m²
#T0_col=79 T0_vor=26 T0_rück=25 T0_sp=T0_col-39

# Pumpe Stufe 1: 4l/min
#Tpump=112 Heizwendel: Mittlere Temperatur: 43.1 °C Energieeintrag: 30.6 Wh Arbeitszahl 21.9 (Atmega8: war mal aktiv, aber nicht so erfolgreich wie Stufe 2)
#Tpump=170 Heizwendel: Mittlere Temperatur: 48.0 °C Energieeintrag: 80.0 Wh Arbeitszahl 37.6 (Atmega8 ab 03.2022)
#Tpump=188 Heizwendel: Mittlere Temperatur: 48.7 °C Energieeintrag: 87.1 Wh Arbeitszahl 37.1 (Optimum laut Simulation)

# Pumpe Stufe 2: 6l/min
#Tpump=103 Heizwendel: Mittlere Temperatur: 46.2 °C Energieeintrag: 61.3 Wh Arbeitszahl 33.0 (Atmega8 bis 03.2022)
#Tpump=120 Heizwendel: Mittlere Temperatur: 47.4 °C Energieeintrag: 74.0 Wh Arbeitszahl 34.2

# Pumpe Stufe 3: 7l/min
#Tpump=102 Heizwendel: Mittlere Temperatur: 47.2 °C Energieeintrag: 71.3 Wh Arbeitszahl 28.0
#Tpump=103 Heizwendel: Mittlere Temperatur: 47.2 °C Energieeintrag: 71.3 Wh Arbeitszahl 27.7


x = np.linspace(dx/2, L_sys-dx/2, N)

dTdt = np.zeros(N)
dTpipe_dt = np.zeros(N)
P_cu = np.zeros(N)
pump_runtime = args.pump_runtime  # start for optimization
tempSens_sol_flow_hot = np.zeros(round(pump_runtime/dt))

pump_runtime_arr = np.arange(pump_runtime, pump_runtime+200,1)
if (args.plot):
    pump_runtime_arr = [pump_runtime]

cnt_decrease = 0
W_max = 0

for pump_runtime in pump_runtime_arr:
    t_arr = np.arange(0, pump_runtime, dt)  # s, simulation time
    
    T_fluid = [np.ones(N_col)*T0_col, np.ones(N_v)*T0_vor, np.ones(N_WT)*T0_sp, np.ones(N_r)*T0_rück]
    T_fluid = np.concatenate(T_fluid)
    T_pipe = np.copy(T_fluid)

    for i,t in enumerate(t_arr):
        if (kill) :
            sys.exit(0)

        if args.plot:
            plt.figure(1)
            plt.clf()

        # Kollektor
        P_cu[0:N_col] = 1*lambda_cu * dx*Ai_col / d_col * (T_fluid[0:N_col]-T_pipe[0:N_col])
        dTpipe_dt[0:N_col] = (P_cu[0:N_col] + P_col/N_col)/(rho_cu*c_cu*dx*Aa_col)
        dTdt[0]       = (m*c_fluid*(T_fluid[N-1]-T_fluid[0])             - P_cu[0]       )/(rho_fluid*c_fluid*dx*Ai_col)
        dTdt[1:N_col] = (m*c_fluid*(T_fluid[0:N_col-1]-T_fluid[1:N_col]) - P_cu[1:N_col] )/(rho_fluid*c_fluid*dx*Ai_col)

        # Vorlauf
        Ns = N_col
        Ne = N_col+N_v
        P_cu[Ns:Ne] = 1*lambda_cu * dx*np.pi*(Di/2)**2 / (Da-Di)/2 * (T_fluid[Ns:Ne]-T_pipe[Ns:Ne])
        dTpipe_dt[Ns:Ne] = P_cu[Ns:Ne]/(rho_cu*c_cu*dx*np.pi*(Da/2)**2-(Di/2)**2)
        dTdt[Ns:Ne] = (m*c_fluid*(T_fluid[Ns-1:Ne-1]-T_fluid[Ns:Ne]) - P_cu[Ns:Ne])/(rho_fluid*c_fluid*dx*np.pi*(Di/2)**2)

        # Wärmetauscher im Trinkwasserspeicher
        Ns += N_v
        Ne += N_WT
        P_cu[Ns:Ne] = 0*lambda_cu * dx*np.pi*(Di_WT/2)**2 / (Da_WT-Di_WT)/2 * (T_fluid[Ns:Ne]-T_pipe[Ns:Ne])
        dTpipe_dt[Ns:Ne] = P_cu[Ns:Ne]/(rho_cu*c_cu*dx*np.pi*(Da_WT/2)**2-(Di_WT/2)**2)
        P = (T_fluid[Ns:Ne]-T0_sp) * lambda_cu * np.pi*(Da_WT+Di_WT)/2*dx / (Da_WT-Di_WT) 
        dTdt[Ns:Ne] = (m*c_fluid*(T_fluid[Ns-1:Ne-1]-T_fluid[Ns:Ne]) - P_cu[Ns:Ne] -0*P )/(rho_fluid*c_fluid*dx*np.pi*(Di_WT/2)**2)

        # Rücklauf
        Ns += N_WT
        Ne += N_r
        P_cu[Ns:Ne] = 1*lambda_cu * dx*np.pi*(Di/2)**2 / (Da-Di)/2 * (T_fluid[Ns:Ne]-T_pipe[Ns:Ne])
        dTpipe_dt[Ns:Ne] = P_cu[Ns:Ne]/(rho_cu*c_cu*dx*np.pi*(Da/2)**2-(Di/2)**2)
        dTdt[Ns:Ne] = (m*c_fluid*(T_fluid[Ns-1:Ne-1]-T_fluid[Ns:Ne]) - P_cu[Ns:Ne])/(rho_fluid*c_fluid*dx*np.pi*(Di/2)**2)


    #    print(T_fluid[N-1], dTdt[0], dTdt[1])

        T_fluid += dTdt*dt
        T_pipe += dTpipe_dt*dt
        
        if args.plot:
            Temp_min = 10
            Temp_max = 90
            plt.figure(1)
            plt.axvline(x=L_col)
            plt.text(0.5, Temp_min+1, f'Collector {L_col:.1f}m', size=14)

            L_VLsens = L_col+L_vor-L_VLsens_Sp
            plt.axvline(x=L_VLsens, color='purple')
            plt.text(L_col+0.5, Temp_min+1, f'Pipe {L_vor:.1f}m', size=14)

            plt.axvline(x=L_col+L_vor)
            plt.text(L_col+L_vor+0.5, Temp_min+1, f'Tank coil {L_WT:.1f}m', size=14)

            plt.axvline(x=L_col+L_vor+L_WT)
            plt.text(L_col+L_vor+L_WT+0.5, Temp_min+1, f'Pipe {L_rück:.1f}m', size=14)

            tempSens_sol_flow_hot[i] = T_pipe[round(L_VLsens/nodes_distance)]
            plt.plot(x,T_fluid, color='blue', label='T_fluid')
            plt.plot(x,T_pipe, color='red', label='T_pipe')
            plt.xlabel('Distance (m)')
            plt.ylabel('Temperature (°C)')
            plt.axis([0, L_sys, Temp_min, Temp_max])
            plt.legend(loc = 'upper left')
            plt.pause(0.000001)
      
    if args.plot:
        plt.figure(2)
        plt.plot(t_arr,tempSens_sol_flow_hot, color='purple', label='tempSens_sol_flow_hot')
        plt.xlabel('Time (s)')
        plt.ylabel('Temperature (°C)')
        plt.legend()

    Tavg_WT = np.average(T_fluid[N_col+N_v:N_col+N_v+N_WT])
    W = (Tavg_WT-T0_sp)*V_WT/1000*rho_fluid*c_fluid/3600
    print('Tpump={:.0f} Heizwendel: Mittlere Temperatur: {:.1f} °C Energieeintrag: {:.1f} Wh Arbeitszahl {:.1f}'.format(pump_runtime, Tavg_WT, W, W/(P_pump*pump_runtime/3600)))
    if W > W_max:
        W_max = W
    else:
        cnt_decrease += 1
        if cnt_decrease == 10:
            break

plt.show()

