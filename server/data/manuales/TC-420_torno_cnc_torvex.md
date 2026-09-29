---
modelo: TC-420
equipo: Torno CNC TORVEX TC-420
fabricante: Torvex Máquinas-Herramienta (ficticio)
alias: torno, torno cnc, torvex
revision: Rev. 5 - 2024
---

# Manual de mantenimiento y alarmas - Torno CNC TORVEX TC-420

> Documento ficticio creado con fines académicos. Los valores no corresponden a ningún equipo comercial real.

## 1. Descripción general

El TORVEX TC-420 es un torno de control numérico de bancada inclinada a 45°, con torreta de 12 posiciones y control TVX-Control 8. Está pensado para mecanizado de piezas de acero, fundición y aluminio en series medianas.

### 1.1 Datos técnicos

| Parámetro | Valor |
|---|---|
| Volteo sobre bancada | 420 mm |
| Longitud máxima de torneado | 650 mm |
| Potencia del husillo principal | 18,5 kW |
| Velocidad máxima del husillo | 4.500 rpm |
| Recorrido eje X / eje Z | 210 mm / 680 mm |
| Presión nominal del sistema hidráulico | 40 bar |
| Depósito de lubricación centralizada de guías | 2 litros |
| Depósito de refrigerante | 180 litros |
| Peso | 4.200 kg |

## 2. Seguridad

- La puerta frontal tiene un enclavamiento de seguridad. Nunca puentear el interruptor de puerta.
- Antes de cambiar insertos, mordazas o realizar mantenimiento, llevar el control a modo EMERGENCIA y aplicar el procedimiento LOTO de la planta.
- El plato hidráulico puede liberar la pieza si cae la presión hidráulica. No operar con la alarma AL-205 activa.
- Usar protección ocular. Las virutas de acero son cortantes y pueden estar calientes.

## 3. Operación

### 3.1 Rutina de calentamiento del husillo

Si la máquina estuvo detenida más de 48 horas (por ejemplo, después de un fin de semana largo), ejecutar el programa de calentamiento O9000 antes de mecanizar:

1. 10 minutos a 1.000 rpm.
2. 10 minutos a 2.500 rpm.
3. 5 minutos a 4.000 rpm.

Esta rutina estabiliza térmicamente los rodamientos del husillo y evita desvíos dimensionales en las primeras piezas. En paradas menores a 48 horas alcanza con 5 minutos a 1.000 rpm.

### 3.2 Referenciado de ejes

Luego de cada encendido, referenciar los ejes en el orden X primero y Z después (modo REF), para evitar colisiones de la torreta con el contrapunto.

## 4. Mantenimiento preventivo

### 4.1 Plan de mantenimiento

| Frecuencia | Tarea |
|---|---|
| Diaria | Verificar nivel del depósito de lubricación de guías, retirar virutas, verificar nivel de refrigerante |
| Semanal | Medir la concentración del refrigerante con refractómetro, limpiar el filtro del tanque de refrigerante |
| Cada 500 horas | Verificar presión hidráulica (40 bar) y limpiar el filtro de aire del tablero eléctrico |
| Cada 2.000 horas | Medir el juego (backlash) de los ejes X y Z y actualizar la compensación en parámetros |
| Cada 4.000 horas | Cambiar aceite hidráulico (ISO VG 32, 25 litros) y el filtro de presión |
| Cada 6 meses | Verificar la nivelación de la bancada con nivel de precisión (tolerancia 0,02 mm/m) |

### 4.2 Lubricación de guías

Utilizar aceite para guías Torvex SlideLub 68 (ISO VG 68). El sistema de lubricación centralizada entrega un pulso cada 15 minutos de movimiento de ejes. Si el depósito llega al nivel mínimo, se activa la alarma AL-310 y la máquina finaliza el ciclo en curso y no permite iniciar uno nuevo.

### 4.3 Refrigerante

El refrigerante es una emulsión de aceite soluble en agua. La concentración correcta es de 5 % a 8 %, medida con refractómetro. Una concentración menor al 5 % favorece la corrosión y el crecimiento bacteriano (olor desagradable); una concentración mayor al 8 % genera espuma y dermatitis en los operarios. Renovar completamente el refrigerante cada 6 meses o antes si presenta olor.

### 4.4 Torques de ajuste

| Elemento | Torque |
|---|---|
| Tornillos de fijación del plato al husillo | 110 N·m |
| Tornillos de mordazas duras | 70 N·m |
| Tornillos de porta-herramientas de la torreta | 35 N·m |

## 5. Alarmas del control TVX-Control 8

| Código | Descripción | Causas probables | Acción correctiva |
|---|---|---|---|
| AL-101 | Sobrecarga del servomotor eje X | Colisión, avance excesivo, guía sin lubricación, husillo de bolas dañado | Verificar colisión, reducir avance, revisar lubricación, medir corriente del servo |
| AL-102 | Sobrecarga del servomotor eje Z | Iguales causas que AL-101 aplicadas al eje Z | Igual procedimiento que AL-101 sobre el eje Z |
| AL-205 | Presión hidráulica baja (menor a 35 bar) | Nivel de aceite hidráulico bajo, fuga, filtro de presión obstruido, bomba desgastada | Detener la máquina, verificar nivel y fugas, reemplazar filtro, regular presión a 40 bar |
| AL-310 | Nivel bajo de lubricación centralizada | Depósito de aceite de guías vacío | Completar con Torvex SlideLub 68 y presionar RESET |
| AL-404 | Puerta abierta durante el ciclo | Apertura de puerta o interruptor de seguridad defectuoso | Cerrar la puerta; si persiste, revisar el interruptor de seguridad |
| AL-500 | Temperatura del husillo alta (mayor a 70 °C) | Falla del enfriador de husillo, rodamientos dañados, sobrecarga sostenida | Verificar el enfriador (chiller), reducir parámetros de corte, consultar al servicio técnico |
| AL-900 | Parada de emergencia activa | Pulsador de emergencia presionado | Identificar la causa, liberar el pulsador girándolo y presionar RESET |

### 5.1 Procedimiento ante AL-205

1. Pulsar parada de ciclo y no intentar liberar la pieza del plato.
2. Verificar el nivel del depósito hidráulico en el visor lateral.
3. Buscar fugas en mangueras del plato y de la torreta.
4. Si el nivel es correcto y no hay fugas, reemplazar el filtro de presión.
5. Regular la presión en la válvula reguladora hasta 40 bar y verificar que se mantenga estable durante 10 minutos.

### 5.2 Síntomas sin alarma

- Mal acabado superficial o vibraciones (chatter): inserto desgastado, voladizo excesivo de la herramienta o rodamientos del husillo con juego.
- Diferencia dimensional en diámetros: falta de compensación de desgaste de herramienta o backlash del eje X sin actualizar.
