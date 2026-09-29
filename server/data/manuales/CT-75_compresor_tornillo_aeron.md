---
modelo: CT-75
equipo: Compresor de tornillo AERON CT-75
fabricante: Aeron Industrial S.A. (ficticio)
alias: compresor, compresor de tornillo, aeron
revision: Rev. 3 - 2025
---

# Manual de operación y mantenimiento - Compresor de tornillo AERON CT-75

> Documento ficticio creado con fines académicos. Los valores no corresponden a ningún equipo comercial real.

## 1. Descripción general

El AERON CT-75 es un compresor de aire rotativo de tornillo, lubricado por inyección de aceite, de una etapa, refrigerado por aire. Está diseñado para servicio industrial continuo (24/7) en plantas metalúrgicas, alimenticias y de plásticos.

### 1.1 Datos técnicos

| Parámetro | Valor |
|---|---|
| Potencia del motor principal | 75 kW (100 HP), 380 V trifásico, 50 Hz |
| Caudal de aire libre (FAD) | 12,5 m³/min a 8 bar |
| Presión máxima de trabajo | 10 bar |
| Presión de trabajo recomendada | 7 a 8,5 bar |
| Temperatura ambiente admisible | 5 °C a 40 °C |
| Temperatura normal de descarga del elemento | 75 °C a 95 °C |
| Capacidad de aceite | 38 litros |
| Nivel sonoro | 72 dB(A) a 1 m |
| Peso | 1.450 kg |

### 1.2 Componentes principales

- Elemento compresor de tornillo asimétrico (rotor macho de 4 lóbulos y hembra de 6 lóbulos).
- Motor eléctrico IE3 con arranque estrella-triángulo.
- Filtro de aire de admisión con prefiltro de espuma.
- Tanque separador aire/aceite con elemento separador coalescente.
- Radiador combinado aire/aceite con ventilador axial.
- Válvula termostática de aceite (apertura a 71 °C).
- Controlador electrónico AERON Smart-C con pantalla de alarmas.

## 2. Seguridad

- Antes de cualquier intervención, detener el equipo desde el controlador, abrir el seccionador principal y aplicar el procedimiento de bloqueo y etiquetado (LOTO) de la planta.
- Despresurizar completamente el circuito: esperar como mínimo 5 minutos después de la parada y verificar que el manómetro del tanque separador marque 0 bar.
- El aceite y las superficies del elemento pueden superar los 90 °C. Usar guantes térmicos.
- Nunca abrir el tapón de llenado de aceite con el equipo presurizado.
- No utilizar el aire comprimido del equipo para respiración humana sin tratamiento específico.

## 3. Operación

### 3.1 Arranque

1. Verificar el nivel de aceite en el visor del tanque separador con el equipo detenido: debe estar entre las marcas MIN y MAX.
2. Verificar que la válvula de salida de aire esté abierta.
3. Presionar START en el controlador. El motor arranca en estrella y, a los 8 segundos, conmuta a triángulo.
4. El compresor comienza a cargar cuando la temperatura del aceite supera los 20 °C.

### 3.2 Parada

Presionar STOP: el equipo descarga durante 30 segundos antes de detener el motor. Utilizar el pulsador de parada de emergencia solamente ante un riesgo real, ya que la parada brusca provoca retorno de aceite hacia el filtro de admisión.

## 4. Mantenimiento preventivo

### 4.1 Plan de mantenimiento por horas

| Intervalo | Tarea |
|---|---|
| Diario | Verificar nivel de aceite, purgar condensado, revisar alarmas |
| Cada 500 horas | Limpiar el prefiltro de espuma y soplar el radiador con aire a baja presión |
| Cada 2.000 horas | Reemplazar filtro de aire y filtro de aceite |
| Cada 4.000 horas o 12 meses (lo que ocurra primero) | Cambio de aceite completo y reemplazo del elemento separador aire/aceite |
| Cada 8.000 horas | Reengrase de rodamientos del motor principal (20 g de grasa por rodamiento) y verificación de la válvula de mínima presión |
| Cada 24.000 horas | Revisión general del elemento compresor por servicio técnico autorizado |

### 4.2 Aceite recomendado

Utilizar exclusivamente aceite sintético AERON LubriScrew 46 (ISO VG 46, base PAO). La mezcla con aceites minerales puede generar espuma y barniz en el elemento. Capacidad total del circuito: 38 litros.

### 4.3 Procedimiento de cambio de aceite

1. Hacer funcionar el equipo 10 minutos para calentar el aceite (se drena mejor en caliente, a unos 60 °C).
2. Detener, aplicar LOTO y despresurizar.
3. Abrir lentamente el tapón de llenado para liberar presión residual.
4. Conectar una manguera a la válvula de drenaje del tanque separador y drenar el aceite en un recipiente adecuado.
5. Reemplazar el filtro de aceite y el elemento separador.
6. Cerrar el drenaje. Torque del tapón de drenaje: 45 N·m.
7. Cargar 38 litros de aceite nuevo hasta la marca MAX del visor.
8. Arrancar, dejar funcionar 5 minutos en carga, detener y reverificar el nivel.
9. Registrar el cambio en el controlador (menú Servicio > Reset contador) para eliminar la advertencia W10.

## 5. Alarmas y diagnóstico

El controlador Smart-C muestra códigos de advertencia (W) que no detienen el equipo y códigos de alarma (A) que provocan parada automática.

| Código | Descripción | Causas probables | Acción correctiva |
|---|---|---|---|
| A01 | Temperatura de descarga alta | Nivel de aceite bajo, radiador obstruido, temperatura ambiente mayor a 40 °C, válvula termostática trabada | Verificar nivel de aceite, limpiar radiador, mejorar ventilación de la sala, revisar válvula termostática |
| A02 | Presión diferencial del separador alta (mayor a 1 bar) | Elemento separador saturado | Reemplazar el elemento separador aire/aceite |
| A03 | Sobrecarga del motor principal | Tensión baja, presión de trabajo excesiva, rodamientos dañados | Medir tensión y corriente, verificar presión de consigna, revisar rodamientos |
| A04 | Secuencia de fases incorrecta | Conexión eléctrica invertida tras una intervención | Invertir dos fases en la alimentación (solo personal eléctrico habilitado) |
| A05 | Sensor de temperatura desconectado | Cable o conector dañado, sensor PT100 defectuoso | Revisar el cableado; reemplazar el sensor PT100 |
| W10 | Mantenimiento programado vencido | Se alcanzó el intervalo de servicio del contador | Realizar el servicio y resetear el contador |
| W12 | Filtro de aire obstruido | Filtro saturado | Limpiar el prefiltro o reemplazar el filtro de aire |

### 5.1 Detalle de la alarma A01

La advertencia de temperatura se activa a 105 °C y la parada por alarma A01 ocurre a 110 °C de temperatura de descarga. No rearmar el equipo más de dos veces consecutivas sin identificar la causa: el funcionamiento repetido a alta temperatura degrada el aceite y puede dañar los rodamientos del elemento. Si la temperatura ambiente de la sala supera los 40 °C, instalar ductos de extracción de aire caliente.

### 5.2 Problemas frecuentes sin código de alarma

- Consumo de aceite excesivo (arrastre de aceite en el aire): separador dañado o línea de retorno de aceite obstruida.
- El compresor no carga: presión de red por encima de la consigna, electroválvula de admisión defectuosa.
- Agua en la red de aire: purgador de condensado trabado o secador frigorífico fuera de servicio.
