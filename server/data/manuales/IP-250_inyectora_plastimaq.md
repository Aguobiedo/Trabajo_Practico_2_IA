---
modelo: IP-250
equipo: Inyectora de plástico PLASTIMAQ IP-250
fabricante: Plastimaq Industrial (ficticio)
alias: inyectora, inyección de plástico, plastimaq
revision: Rev. 2 - 2025
---

# Manual técnico - Inyectora de plástico PLASTIMAQ IP-250

> Documento ficticio creado con fines académicos. Los valores no corresponden a ningún equipo comercial real.

## 1. Descripción general

La PLASTIMAQ IP-250 es una máquina inyectora horizontal de termoplásticos con cierre por rodilleras (toggle) de cinco puntos, accionamiento hidráulico con bomba de caudal variable y control PQ-Touch.

### 1.1 Datos técnicos

| Parámetro | Valor |
|---|---|
| Fuerza de cierre | 250 toneladas |
| Diámetro del husillo | 50 mm |
| Capacidad de inyección (PS) | 480 g |
| Presión máxima del sistema hidráulico | 175 bar |
| Zonas de calefacción del barril | 5 zonas + boquilla |
| Aceite hidráulico | ISO VG 46 HM (antidesgaste), tanque de 320 litros |
| Temperatura operativa del aceite hidráulico | 35 °C a 50 °C |
| Potencia del motor de la bomba | 30 kW |

## 2. Seguridad

- La máquina tiene tres niveles de protección de la zona de molde: interruptor eléctrico de puerta, válvula hidráulica de seguridad y traba mecánica. Verificar su funcionamiento al inicio de cada turno abriendo la puerta con la máquina en ciclo manual: el movimiento de cierre debe detenerse de inmediato.
- El barril y la boquilla trabajan a más de 200 °C. Usar careta facial y guantes térmicos durante la purga.
- Antes de ingresar a la zona de molde para mantenimiento, apagar la bomba, aplicar el procedimiento LOTO y descargar la presión de los acumuladores.

## 3. Operación

### 3.1 Temperaturas de procesamiento recomendadas

| Material | Temperatura del barril | Temperatura de molde |
|---|---|---|
| Polipropileno (PP) | 200 °C a 250 °C | 20 °C a 50 °C |
| Polietileno de alta densidad (PEAD) | 190 °C a 240 °C | 20 °C a 40 °C |
| ABS | 210 °C a 240 °C | 50 °C a 70 °C |
| Poliamida 6 (PA6) | 240 °C a 270 °C | 60 °C a 90 °C |

La poliamida y el ABS deben secarse antes de procesarse (PA6: 4 horas a 80 °C; ABS: 2 horas a 80 °C).

### 3.2 Purga y cambio de material

1. Retirar la unidad de inyección del molde (boquilla separada).
2. Vaciar la tolva y cerrar la compuerta de alimentación.
3. Inyectar en vacío (purga) hasta que salga el material anterior completamente.
4. Cargar compuesto de purga si el cambio es de un material oscuro a uno claro.
5. Cargar el nuevo material y purgar hasta obtener un color homogéneo.

### 3.3 Cambio de molde

1. Abrir la máquina completamente y colocar las bridas de sujeción del molde.
2. Ajustar la altura de molde desde el menú Molde > Ajuste automático de altura.
3. Torque de los tornillos de las bridas de sujeción (M20): 250 N·m.
4. Conectar el circuito de refrigeración del molde y verificar ausencia de fugas.
5. Configurar la protección de molde (baja presión de cierre) antes del primer ciclo.

## 4. Mantenimiento preventivo

| Intervalo | Tarea |
|---|---|
| Cada turno | Verificar protecciones de seguridad y temperatura del aceite hidráulico |
| Cada 250 horas | Verificar el engrase automático de las rodilleras; completar el depósito de grasa (grasa de litio EP2) |
| Cada 1.000 horas | Limpiar el intercambiador de calor de aceite, revisar mangueras hidráulicas |
| Cada 2.500 horas | Reemplazar el filtro de retorno del sistema hidráulico |
| Cada 5.000 horas | Análisis de laboratorio del aceite hidráulico (contaminación ISO 4406 máxima: 18/16/13) |
| Cada 10.000 horas | Cambio completo de aceite hidráulico (320 litros) si el análisis no indicó antes |
| Anual | Medir el desgaste del husillo y del barril (juego máximo admisible: 0,25 mm) |

## 5. Códigos de error del control PQ-Touch

| Código | Descripción | Causas probables | Acción correctiva |
|---|---|---|---|
| E-05 | Temperatura de zona del barril fuera de rango | Resistencia calefactora quemada, contactor de estado sólido defectuoso | Medir la resistencia (valor nominal 32 ohm por banda); reemplazar resistencia o contactor |
| E-12 | Temperatura del aceite hidráulico alta (mayor a 55 °C) | Intercambiador de calor sucio, falta de agua de refrigeración, válvula de agua cerrada | Verificar caudal de agua de refrigeración y limpiar el intercambiador |
| E-17 | Falla de termocupla (lectura abierta) en una zona del barril | Termocupla cortada, conector flojo, cable dañado por temperatura | Ver procedimiento 5.1 |
| E-21 | Presión de inyección no alcanzada | Válvula antirretorno del husillo desgastada, fuga interna, material frío | Verificar temperaturas, revisar la válvula antirretorno (anillo check) |
| E-30 | Protección de molde activada | Pieza o colada atrapada entre las placas del molde | Abrir el molde, retirar la obstrucción y revisar el expulsor |
| E-44 | Lubricación de rodilleras insuficiente | Depósito de grasa vacío, bomba de engrase o dosificador obstruido | Completar grasa EP2 y verificar el dosificador de cada punto |

### 5.1 Procedimiento ante E-17 (falla de termocupla)

1. Identificar en pantalla la zona afectada (la alarma indica el número de zona).
2. Con la máquina en modo manual, verificar el conector de la termocupla en la caja de conexiones de la zona.
3. Medir la termocupla con multímetro: una termocupla tipo J sana tiene continuidad (resistencia baja, menor a 10 ohm). Si el circuito está abierto, reemplazarla.
4. Al reemplazar, usar termocupla tipo J de bayoneta, 6 mm, con la misma longitud de inmersión.
5. Mientras la zona esté sin termocupla, la calefacción de esa zona queda deshabilitada. No operar la máquina en modo "porcentaje fijo" por más de 1 hora, ya que la zona puede sobrecalentarse y degradar el material.

### 5.2 Defectos de pieza frecuentes

| Defecto | Causa probable | Corrección |
|---|---|---|
| Rechupes | Presión o tiempo de mantenimiento insuficiente | Aumentar presión y tiempo de mantenimiento |
| Rebabas | Fuerza de cierre insuficiente o molde dañado | Aumentar fuerza de cierre, revisar el plano de partición |
| Pieza incompleta | Material frío o dosificación insuficiente | Aumentar temperatura o carrera de dosificación |
| Quemaduras (marcas negras) | Aire atrapado, velocidad de inyección excesiva | Reducir velocidad, mejorar venteo del molde |
