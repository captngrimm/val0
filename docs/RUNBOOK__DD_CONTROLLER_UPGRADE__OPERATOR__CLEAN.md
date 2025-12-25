# DD Controller Upgrade — OPERATOR Runbook (VFMS v0, grounded)
**Rule:** Do not invent steps. If a required detail is missing, log it in docs/GAPS__DD_CONTROLLER_UPGRADE.md and STOP.
**Primary source:** TA-ControllerUpgrade_Telefonica_DD9900.pdf (doc_id 20251224_130922_532031)
**Stitched source:** docs/RUNBOOK__DD_CONTROLLER_UPGRADE__STITCHED.md

---

## 5.1 APAGAR LA CONTROLADORA ORIGEN (Shutdown source controller)
### Preconditions (hard stops)
- Filesystem usage must be < 95% (per procedure text)
- Stop all backup operations to the source system
- Review and correct any active alerts
- Poweroff: do NOT power off shelves/trays (“No apagar las bandejas.”)


### Evidence
# VFMS v0 Grounded Output

**Requirement:** Filesystem must be below 95% utilization.

por debajo del 95% de ocupación.

**Verification command and output:**

filesys show space

Active Tier:
Resource           Size GiB     Used GiB   Avail GiB   Use%   Cleanable GiB*
----------------   --------   ----------   ---------   ----   --------------
/data: post-comp   688292.9     456889.6    231403.3    66%          24640.7
/ddvar                 49.1         17.6        29.0    38%
/ddvar/core          1215.2          1.1      1152.4     0%


## 5.2 CAMBIO FÍSICO DE CONTROLADORA (Physical swap)
**NOTE:** This section must come from the “cambio físico” summary output.
### Evidence
# VFMS v0 Grounded Output

**Query:** CAMBIO FÍSICO

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0005

5      ***CAMBIO DE CONTROLADORA .......................................................................................... 38
             5.1        APAGAR LA CONTROLADORA ORIGEN ............................................................................................ 38
             5.2        CAMBIO FÍSICO DE CONTROLADORA .............................................................................................. 42
             5.3        CONFIGURAR LA CONTROLADORA DE DESTINO ............................................................................. 44
             5.4        RECUPERAR Y VERIFICAR LA CONFIGURACIÓN SCSI TARGET ....................................................... 54
             5.5        VERIFICACIÓN DE LA CONFIGURACIÓN CLOUD TIER ..................................................................... 56
             5.6        VERIFICAR LA CONFIGURACIÓN DE RED Y CONECTIVIDAD ............................................................ 57
             5.7        VERIFICAR LA CONECTIVIDAD CIFS, NFS Y DDBOOST ................................................................ 59
             5.8        VERIFICAR EL ESTADO DEL FILE SYSTEM ....................................................................................... 60
             5.9        VERIFICAR EL ESTADO DE LA REPLICACIÓN ................................................................................... 61
             5.10       ACTUALIZAR LA CONFIGURACIÓN DE IPMI ...........

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0128

ystem poweroff
                               sysadmin@vdc-dd5# system poweroff

                               The 'system poweroff' command shutdowns the system and turns off the power.
                               Are you sure? (yes|no) [no]: yes

                               ok, proceeding.

                               The system is going down.


                               Broadcast message from root (Tue Jul 11 10:23:05 2023):




                               The system is going down for system halt NOW!



                               Broadcast message from root (Tue Jul 11 10:23:05 2023):




                               The system is going down for system halt NOW!


                               INIT: Switching
                               INIT: Sending processes the TERM signal

                               sysadmin@vdc-dd5#




Controller upgrade
                                                                 41/69
  Dell Customer Communication - Confidential




                      5.2 CAMBIO FÍSICO DE CONTROLADORA
                     NOTA: Una vez que el sistema destino ha sido instalado e iniciado, el proceso de
                     upgrade no puede ser detenido. En ese caso la integridad de los datos puede verse
                     afectado.

                     Los pasos por seguir para el cambio de la controladora se identifican a continuación.


                          1. Etiquetar todos los cables en la controladora origen (94

---
_Generated manually from indexed chunks. No background processing._

---

## 5.3 CONFIGURAR LA CONTROLADORA DE DESTINO (Configure destination controller)
### Evidence
# VFMS v0 Grounded Output

**Query:** CONFIGURAR LA CONTROLADORA DE DESTINO

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0005

5      ***CAMBIO DE CONTROLADORA .......................................................................................... 38
             5.1        APAGAR LA CONTROLADORA ORIGEN ............................................................................................ 38
             5.2        CAMBIO FÍSICO DE CONTROLADORA .............................................................................................. 42
             5.3        CONFIGURAR LA CONTROLADORA DE DESTINO ............................................................................. 44
             5.4        RECUPERAR Y VERIFICAR LA CONFIGURACIÓN SCSI TARGET ....................................................... 54
             5.5        VERIFICACIÓN DE LA CONFIGURACIÓN CLOUD TIER ..................................................................... 56
             5.6        VERIFICAR LA CONFIGURACIÓN DE RED Y CONECTIVIDAD ............................................................ 57
             5.7        VERIFICAR LA CONECTIVIDAD CIFS, NFS Y DDBOOST ................................................................ 59
             5.8        VERIFICAR EL ESTADO DEL FILE SYSTEM ....................................................................................... 60
             5.9        VERIFICAR EL ESTADO DE LA REPLICACIÓN ................................................................................... 61
             5.10       ACTUALIZAR LA CONFIGURACIÓN DE IPMI ...........

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0131

--------------------------------------------

                              NVRAM Batteries:

                                      Card     Battery   Status    Charge     Charging   Time To       Temperature   Voltage

                                                                              Status     Full Charge

                                      ----     -------   ------      ------   --------   -----------   -----------   -------

                                      1        1         ok        100 %      enabled    0 mins        31 C          4.180 V

                                      ----     -------   ------      ------   --------   -----------   -----------   -------

                              sysadmin@localhost#




Controller upgrade
                                                                   43/69
  Dell Customer Communication - Confidential




                     5.3 CONFIGURAR LA CONTROLADORA DE DESTINO
                          1. Revisar las alertas del sistema.

                              system show serial
                              alerts show current


                          2. Revisar la topología del sistema.

                              enclosure show topology

                              La topología se reorganiza después del “system headswap” automáticamente.
                               sysadmin@localhost# enclosure show topology
                               Port       enc.ctrl.port       enc.ctrl.port

---
_Generated manually from indexed chunks. No background processing._

---

## 5.4 RECUPERAR Y VERIFICAR CONFIGURACIÓN SCSI TARGET
### Evidence
# VFMS v0 Grounded Output

**Query:** RECUPERAR Y VERIFICAR LA CONFIGURACIÓN SCSI TARGET

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0005

5      ***CAMBIO DE CONTROLADORA .......................................................................................... 38
             5.1        APAGAR LA CONTROLADORA ORIGEN ............................................................................................ 38
             5.2        CAMBIO FÍSICO DE CONTROLADORA .............................................................................................. 42
             5.3        CONFIGURAR LA CONTROLADORA DE DESTINO ............................................................................. 44
             5.4        RECUPERAR Y VERIFICAR LA CONFIGURACIÓN SCSI TARGET ....................................................... 54
             5.5        VERIFICACIÓN DE LA CONFIGURACIÓN CLOUD TIER ..................................................................... 56
             5.6        VERIFICAR LA CONFIGURACIÓN DE RED Y CONECTIVIDAD ............................................................ 57
             5.7        VERIFICAR LA CONECTIVIDAD CIFS, NFS Y DDBOOST ................................................................ 59
             5.8        VERIFICAR EL ESTADO DEL FILE SYSTEM ....................................................................................... 60
             5.9        VERIFICAR EL ESTADO DE LA REPLICACIÓN ................................................................................... 61
             5.10       ACTUALIZAR LA CONFIGURACIÓN DE IPMI ...........

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0158

o correctamente, aunque se indica un mismatch por que
                              el número de serie del Data Domain cambia y han de ser regularizadas en menos de
                              30 días solicitando un Rehost.

                              En los siguientes modelos de Data Domain la Cache Tier está habilitada por defecto y no
                              requieren licencia.




Controller upgrade
                                                                    52/69
  Dell Customer Communication - Confidential




                          18. Bajo ciertas circustancias puede ser preciso agregar de nuevo las claves ssh de los sistemas
                              Avamar para su usuario de conexión ddboost.




Controller upgrade
                                                               53/69
  Dell Customer Communication - Confidential




                      5.4 RECUPERAR Y VERIFICAR LA CONFIGURACIÓN SCSI TARGET

                     Si en la controladora origen estaba configurado VTL o DDBoost over FC utilizar el
                     siguiente procedimiento para verificar y/o recuperar la configuración.
                          1. Habilitar SCSITARGET.

                              scsitarget status
                              scsitarget enable
                               sysadmin@vdc-dd5# scsitarget status
                               SCSI Target subsystem admin state: disabled, process is stopped, modules unloaded.

---
_Generated manually from indexed chunks. No background processing._

# VFMS v0 Grounded Output

**Query:** scsitarget

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0029

e grupos de DDBoost FC.

                              OK, no.

                              ddboost fc group show detailed
                               DELLEMC@vdc-dd5# ddboost fc group show detailed
                               DDBoost FC Groups could not be listed

                               **** DFCUSER is not running

                               DELLEMC@vdc-dd5#




                          12. Obtener la configuración de “scsitarget”.

                              OK, no.

                              scsitarget port show detailed
                              scsitarget group show detailed
                              scsitarget endpoint show detailed
                              scsitarget initiator show detailed
                              scsitarget transport option show all
                              scsitarget endpoint show list
                               sysadmin@vdc-dd5# scsitarget port show detailed
                               No matching ports were found.
                               sysadmin@vdc-dd5# scsitarget endpoint show detailed
                               No matching endpoints were found.
                               sysadmin@vdc-dd5# scsitarget initiator show detailed
                               No matching initiators were found.
                               sysadmin@vdc-dd5# scsitarget endpoint show list
                               No matching endpoints were found.
                               sysadmin@vdc

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0030

in@vdc-dd5# scsitarget endpoint show list
                               No matching endpoints were found.
                               sysadmin@vdc-dd5#

                          13. Crear una tabla de endpoints.

                              OK, no.

                              El nombre de endpoint , WWPN y WWNN son transferidos a la controladora destino
                              (DD9900) durante el upgrade. Utilizar la tabla creada para borrar los nuevos endpoints y
                              reasignar los endpoints migrados al puerto correcto en caso de no coincidencia. Construir
                              la tabla en base a la salida de “system show ports”.

                              Endpoint   WWPN       WWNN     Source Port   Destination Port




Controller upgrade
                                                                  18/69
  Dell Customer Communication - Confidential




                          14. Obtener la configuración de réplica.

                              OK, no.

                              replication show config
                               DELLEMC@vdc-dd5# replication show config
                               **** This restorer is not configured for replication.
                               DELLEMC@vdc-dd5#

                          15. Obtener la configuración de NFS y DD Boost.

                              OK.

                              Aunque no debe ser necesaria este tipo de reconfiguración se recomi

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0123

limpieza de Cloud Tier.

                              data-movement status
                              data-movement stop




Controller upgrade
                                                                38/69
  Dell Customer Communication - Confidential




                              cloud clean status
                              cloud clean stop


                          7. Deshabilitar VTL.

                              vtl status
                              vtl disable
                               sysadmin@vdc-dd5# vtl status
                               VTL admin_state: disabled, process_state: stopped, licensed
                               sysadmin@vdc-dd5#

                          8. Si SCSI Target está habilitado, deshabilitarlo.

                              scsitarget status
                              scsitarget disable
                               sysadmin@vdc-dd5# scsitarget status
                               SCSI Target subsystem admin state: enabled, process is running, modules loaded.
                               sysadmin@vdc-dd5# scsitarget disable
                               Please wait...
                               SCSI Target subsystem is disabled.

                               sysadmin@vdc-dd5#

                          9. Si hay conexiones DDBoost, detener las operativas de los softwares de backup. Identificar
                             los sistemas utilizando

                              ddb

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0124

detener las operativas de los softwares de backup. Identificar
                             los sistemas utilizando

                              ddboost show connections


                          10. Determinar si la replicación está habilitada y deshabilitarla. No continuar hasta que la
                              replicación esté deshabilitada en todos los contextos.

                              replication status
                              replication disable all
                              replication status


                          11. Verificar que no hay tráfico en las tarjetas de red, ejecutarlo durante 60 segundos.

                              iostat 2


                          12. Verificar que no hay tráfico en los puertos FC.

                              scsitarget initiator show stats interval 2 count 60


                          13. Verificar las conexiones NFS, desmontar los file system en los servidores cliente y
                              deshabilitar NFS.




Controller upgrade
                                                               39/69
  Dell Customer Communication - Confidential




                              nfs show active
                              nfs disable
                               sysadmin@vdc-dd5# nfs show active
                               Path                                                         Client
                               ----------------------------------------------------------

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0158

o correctamente, aunque se indica un mismatch por que
                              el número de serie del Data Domain cambia y han de ser regularizadas en menos de
                              30 días solicitando un Rehost.

                              En los siguientes modelos de Data Domain la Cache Tier está habilitada por defecto y no
                              requieren licencia.




Controller upgrade
                                                                    52/69
  Dell Customer Communication - Confidential




                          18. Bajo ciertas circustancias puede ser preciso agregar de nuevo las claves ssh de los sistemas
                              Avamar para su usuario de conexión ddboost.




Controller upgrade
                                                               53/69
  Dell Customer Communication - Confidential




                      5.4 RECUPERAR Y VERIFICAR LA CONFIGURACIÓN SCSI TARGET

                     Si en la controladora origen estaba configurado VTL o DDBoost over FC utilizar el
                     siguiente procedimiento para verificar y/o recuperar la configuración.
                          1. Habilitar SCSITARGET.

                              scsitarget status
                              scsitarget enable
                               sysadmin@vdc-dd5# scsitarget status
                               SCSI Target subsystem admin state: disabled, process is stopped, modules unloaded.

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0159

scsitarget status
                               SCSI Target subsystem admin state: disabled, process is stopped, modules unloaded.
                               sysadmin@vdc-dd5# scsitarget enable
                               Please wait...
                               SCSI Target subsystem is enabled.

                               sysadmin@vdc-dd5#

                          2. Si VTL estaba habilitado en el sistema original, habilitarlo.

                              vtl status
                              vtl enable


                          3. Mostar la información de Fibre Channel.

                              system show ports
                              scsitarget endpoint show detailed
                              scsitarget port show detailed


                              Se puede ver esta información en el autosupport buscando “SCSITARGET
                              Endpoint Show Detailed”.

                              *Contrastar esta información con la salida “SCSITARGET Port Show Detailed
                              All” y el campo “FC Current WWPN”, o mejor con “system show ports”.

                              *Configuración en controladora origen (DD9400)
                              Endpoint     WWPN    WWNN     Source Port   Destination Port




                          4. Si es preciso actualizar la configuración SCSI seguir los siguientes pasos.

                              La configuración scsi se ha migrado correctamente.

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0160

ciso actualizar la configuración SCSI seguir los siguientes pasos.

                              La configuración scsi se ha migrado correctamente.

                                  a. Mostrar la lista de endpoints actual.

                                         scsitarget endpoint show list




Controller upgrade
                                                                 54/69
  Dell Customer Communication - Confidential




                                       *Configuración en controladora origen (DD9400)

                                  b. Deshabilitar todos los endpoints.

                                       scsitarget endpoint disable all


                                  c. Borrar todos los endpoint, para cada endpoint a borrar:

                                       scsitarget endpoint del     endpoint-spec



                                  d. Renombrar los endpoint con el nombre en el sistema origen.

                                       scsitarget endpoint show list
                                       scsitarget endpoint modify endpointfc-0 system-address 5a
                                       scsitarget endpoint modify endpointfc-1 system-address 5b
                                       scsitarget endpoint modify endpointfc-2 system-address 6a
                                       scsitarget endpoint modify endpointfc-3 system-address 6b


                                       Si es preciso cambiar los wwpn utilizar

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0161

itarget endpoint modify endpointfc-3 system-address 6b


                                       Si es preciso cambiar los wwpn utilizar

                                       scsitarget endpoint modify [endpoint-spec] wwpn [wwpn] wwnn [wwnn]
                                       scsitarget endpoint modify [endpoint-spec] wwpn [wwpn] wwnn [wwnn]
                                       scsitarget endpoint modify [endpoint-spec] wwpn [wwpn] wwnn [wwnn]
                                       scsitarget endpoint modify [endpoint-spec] wwpn [wwpn] wwnn [wwnn]
                                       scsitarget endpoint modify [endpoint-spec] wwpn [wwpn] wwnn [wwnn]
                                  e. Verificar la configuración de endpoints.

                                       scsitarget endpoint show detailed


# VFMS v0 Grounded Output

**Query:** vtl group show

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0162

ables FC SAN.

                          6. Verificar que todos los dispositivos son visibles en el grupo con los nuevos puertos.

                              vtl group show all
                              vtl group show groupname


                          7. Verificar que todas las opciones de VTL se han configurado correctamente.

                              vtl option show all
                              vtl show config


                          8. Actualizar los “access groups” con el puerto primario y secundario configurado para todos
                             los “access groups” basados en mapping FC si es preciso.

                              scsitarget group show list
                              scsitarget group modify


                              *Configuración en controladora origen (DD9400)




                      5.5 VERIFICACIÓN DE LA CONFIGURACIÓN CLOUD TIER
                     Si Cloud Tier estaba configurado en el sistema origen, verificar que está correctamente
                     configurado en el sistema destino con el siguiente procedimiento.
                          1. Revisar la salida de los siguientes comandos.

                              storage show all
                              cloud unit list
                              cloud profile show all
                              cloud clean frequency show
                              cloud clean throttle show
                              data-movement policy show

---
_Generated manually from indexed chunks. No background processing._

---

## 5.5 VERIFICACIÓN CONFIGURACIÓN CLOUD TIER
### Evidence
# VFMS v0 Grounded Output

**Query:** VERIFICACIÓN DE LA CONFIGURACIÓN CLOUD TIER

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0005

5      ***CAMBIO DE CONTROLADORA .......................................................................................... 38
             5.1        APAGAR LA CONTROLADORA ORIGEN ............................................................................................ 38
             5.2        CAMBIO FÍSICO DE CONTROLADORA .............................................................................................. 42
             5.3        CONFIGURAR LA CONTROLADORA DE DESTINO ............................................................................. 44
             5.4        RECUPERAR Y VERIFICAR LA CONFIGURACIÓN SCSI TARGET ....................................................... 54
             5.5        VERIFICACIÓN DE LA CONFIGURACIÓN CLOUD TIER ..................................................................... 56
             5.6        VERIFICAR LA CONFIGURACIÓN DE RED Y CONECTIVIDAD ............................................................ 57
             5.7        VERIFICAR LA CONECTIVIDAD CIFS, NFS Y DDBOOST ................................................................ 59
             5.8        VERIFICAR EL ESTADO DEL FILE SYSTEM ....................................................................................... 60
             5.9        VERIFICAR EL ESTADO DE LA REPLICACIÓN ................................................................................... 61
             5.10       ACTUALIZAR LA CONFIGURACIÓN DE IPMI ...........

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0162

ables FC SAN.

                          6. Verificar que todos los dispositivos son visibles en el grupo con los nuevos puertos.

                              vtl group show all
                              vtl group show groupname


                          7. Verificar que todas las opciones de VTL se han configurado correctamente.

                              vtl option show all
                              vtl show config


                          8. Actualizar los “access groups” con el puerto primario y secundario configurado para todos
                             los “access groups” basados en mapping FC si es preciso.

                              scsitarget group show list
                              scsitarget group modify


                              *Configuración en controladora origen (DD9400)




                      5.5 VERIFICACIÓN DE LA CONFIGURACIÓN CLOUD TIER
                     Si Cloud Tier estaba configurado en el sistema origen, verificar que está correctamente
                     configurado en el sistema destino con el siguiente procedimiento.
                          1. Revisar la salida de los siguientes comandos.

                              storage show all
                              cloud unit list
                              cloud profile show all
                              cloud clean frequency show
                              cloud clean throttle show
                              data-movement policy show

---
_Generated manually from indexed chunks. No background processing._

# VFMS v0 Grounded Output

**Query:** data-movement status

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0025

DELLEMC@vdc-dd5#




                          5. Suspender las operativas de “space reclamation”.

                              OK, no.

                              archive space-reclamation status
                              archive space-reclamation suspend
                               sysadmin@dd-hostname-origen# archive space-reclamation status

                               **** Archiver is not enabled. This operation is supported only when archiver is enabled.

                               sysadmin@dd-hostname-origen#



                          6. Verificar si existe Cloud Tier y si el Data Domain destino (DD9900) lo soporta.

                              OK, no.

                              storage show tier cloud
                               DELLEMC@vdc-dd5# storage show tier cloud
                               DELLEMC@vdc-dd5#




                          7. Asegurarse que no existe movimiento de datos.

                              OK, no.

                              data-movement status
                              data-movement stop all




Controller upgrade
                                                                    16/69
  Dell Customer Communication - Confidential




                               DELLEMC@vdc-dd5# data-movement status

                               **** Cloud feature is not enabled. This operation is supported only when cloud feature is
                               enabled.

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0122

2. Detener todas las operativas de los softwares de backup sobre el Data Domain origen
                             (9400).

                          3. Revisar las alertas del sistema y corregirlas si existen.

                              alerts show current
                               sysadmin@vdc-dd5# alerts show current
                               No active alerts.
                               sysadmin@vdc-dd5#

                          4. Revisar si existen multiples unidades de “archive”, si es así se deben unir en una.

                              Nota: Los sistemas con unidades de archivado o “Extended Retention” no pueden ser
                              actualizados a DD6900, DD9400, and DD9900.

                              filesys archive unit list all


                          5. Para sistemas con “Extended Retention” detener las operativas de “data-movement” y
                             “space-reclamation”.

                              archive data-movement status
                              archive data-movement stop
                              archive space-reclamation status
                              archive space-reclamation suspend



                          6. Para sistemas con “Cloud Tier” detener las operativas “data-movement” y los procesos de
                             limpieza de Cloud Tier.

                              data-movement status
                              data-movement stop




Controlle

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0123

limpieza de Cloud Tier.

                              data-movement status
                              data-movement stop




Controller upgrade
                                                                38/69
  Dell Customer Communication - Confidential




                              cloud clean status
                              cloud clean stop


                          7. Deshabilitar VTL.

                              vtl status
                              vtl disable
                               sysadmin@vdc-dd5# vtl status
                               VTL admin_state: disabled, process_state: stopped, licensed
                               sysadmin@vdc-dd5#

                          8. Si SCSI Target está habilitado, deshabilitarlo.

                              scsitarget status
                              scsitarget disable
                               sysadmin@vdc-dd5# scsitarget status
                               SCSI Target subsystem admin state: enabled, process is running, modules loaded.
                               sysadmin@vdc-dd5# scsitarget disable
                               Please wait...
                               SCSI Target subsystem is disabled.

                               sysadmin@vdc-dd5#

                          9. Si hay conexiones DDBoost, detener las operativas de los softwares de backup. Identificar
                             los sistemas utilizando

                              ddb

---
_Generated manually from indexed chunks. No background processing._

# VFMS v0 Grounded Output

**Query:** data-movement stop

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0025

DELLEMC@vdc-dd5#




                          5. Suspender las operativas de “space reclamation”.

                              OK, no.

                              archive space-reclamation status
                              archive space-reclamation suspend
                               sysadmin@dd-hostname-origen# archive space-reclamation status

                               **** Archiver is not enabled. This operation is supported only when archiver is enabled.

                               sysadmin@dd-hostname-origen#



                          6. Verificar si existe Cloud Tier y si el Data Domain destino (DD9900) lo soporta.

                              OK, no.

                              storage show tier cloud
                               DELLEMC@vdc-dd5# storage show tier cloud
                               DELLEMC@vdc-dd5#




                          7. Asegurarse que no existe movimiento de datos.

                              OK, no.

                              data-movement status
                              data-movement stop all




Controller upgrade
                                                                    16/69
  Dell Customer Communication - Confidential




                               DELLEMC@vdc-dd5# data-movement status

                               **** Cloud feature is not enabled. This operation is supported only when cloud feature is
                               enabled.

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0122

2. Detener todas las operativas de los softwares de backup sobre el Data Domain origen
                             (9400).

                          3. Revisar las alertas del sistema y corregirlas si existen.

                              alerts show current
                               sysadmin@vdc-dd5# alerts show current
                               No active alerts.
                               sysadmin@vdc-dd5#

                          4. Revisar si existen multiples unidades de “archive”, si es así se deben unir en una.

                              Nota: Los sistemas con unidades de archivado o “Extended Retention” no pueden ser
                              actualizados a DD6900, DD9400, and DD9900.

                              filesys archive unit list all


                          5. Para sistemas con “Extended Retention” detener las operativas de “data-movement” y
                             “space-reclamation”.

                              archive data-movement status
                              archive data-movement stop
                              archive space-reclamation status
                              archive space-reclamation suspend



                          6. Para sistemas con “Cloud Tier” detener las operativas “data-movement” y los procesos de
                             limpieza de Cloud Tier.

                              data-movement status
                              data-movement stop




Controlle

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0123

limpieza de Cloud Tier.

                              data-movement status
                              data-movement stop




Controller upgrade
                                                                38/69
  Dell Customer Communication - Confidential




                              cloud clean status
                              cloud clean stop


                          7. Deshabilitar VTL.

                              vtl status
                              vtl disable
                               sysadmin@vdc-dd5# vtl status
                               VTL admin_state: disabled, process_state: stopped, licensed
                               sysadmin@vdc-dd5#

                          8. Si SCSI Target está habilitado, deshabilitarlo.

                              scsitarget status
                              scsitarget disable
                               sysadmin@vdc-dd5# scsitarget status
                               SCSI Target subsystem admin state: enabled, process is running, modules loaded.
                               sysadmin@vdc-dd5# scsitarget disable
                               Please wait...
                               SCSI Target subsystem is disabled.

                               sysadmin@vdc-dd5#

                          9. Si hay conexiones DDBoost, detener las operativas de los softwares de backup. Identificar
                             los sistemas utilizando

                              ddb

---
_Generated manually from indexed chunks. No background processing._

---

## 5.6 VERIFICAR RED Y CONECTIVIDAD
### Evidence
# VFMS v0 Grounded Output

**Query:** VERIFICAR LA CONFIGURACIÓN DE RED

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0005

5      ***CAMBIO DE CONTROLADORA .......................................................................................... 38
             5.1        APAGAR LA CONTROLADORA ORIGEN ............................................................................................ 38
             5.2        CAMBIO FÍSICO DE CONTROLADORA .............................................................................................. 42
             5.3        CONFIGURAR LA CONTROLADORA DE DESTINO ............................................................................. 44
             5.4        RECUPERAR Y VERIFICAR LA CONFIGURACIÓN SCSI TARGET ....................................................... 54
             5.5        VERIFICACIÓN DE LA CONFIGURACIÓN CLOUD TIER ..................................................................... 56
             5.6        VERIFICAR LA CONFIGURACIÓN DE RED Y CONECTIVIDAD ............................................................ 57
             5.7        VERIFICAR LA CONECTIVIDAD CIFS, NFS Y DDBOOST ................................................................ 59
             5.8        VERIFICAR EL ESTADO DEL FILE SYSTEM ....................................................................................... 60
             5.9        VERIFICAR EL ESTADO DE LA REPLICACIÓN ................................................................................... 61
             5.10       ACTUALIZAR LA CONFIGURACIÓN DE IPMI ...........

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0163

cloud clean frequency show
                              cloud clean throttle show
                              data-movement policy show
                              data-movement schedule show
                              data-movement throttle show


                          2. Si la limpieza “cloud” fue detenida, iniciarla.

                              cloud clean start <cloud-unit-name>
                              cloud clean status




Controller upgrade
                                                              56/69
  Dell Customer Communication - Confidential




                          3. Verificar que la “passphrase” es la misma que antes del “headswap”.

                              system passphrase set




                     5.6 VERIFICAR LA CONFIGURACIÓN DE RED Y CONECTIVIDAD
                          1. Revisar la configuración actual y compararla con la configuración previa.

                              La configuración del puerto eth1b se ha pasado al puerto eth10b.

                              *Con el “headswap” las direcciones MAC no se trasladan al nuevo sistema.

                              net show hardware
                              net show settings

                              *Configuración en controladora origen (DD9400)
                              Source Port   Speed     Physical   Link Status     State      Destination Port
                                 eth1b      10Gb/s     Fiber        yes         running

---
_Generated manually from indexed chunks. No background processing._

---

## 5.7 VERIFICAR CIFS / NFS / DDBOOST
### Evidence
# VFMS v0 Grounded Output

**Query:** VERIFICAR LA CONECTIVIDAD CIFS

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0005

5      ***CAMBIO DE CONTROLADORA .......................................................................................... 38
             5.1        APAGAR LA CONTROLADORA ORIGEN ............................................................................................ 38
             5.2        CAMBIO FÍSICO DE CONTROLADORA .............................................................................................. 42
             5.3        CONFIGURAR LA CONTROLADORA DE DESTINO ............................................................................. 44
             5.4        RECUPERAR Y VERIFICAR LA CONFIGURACIÓN SCSI TARGET ....................................................... 54
             5.5        VERIFICACIÓN DE LA CONFIGURACIÓN CLOUD TIER ..................................................................... 56
             5.6        VERIFICAR LA CONFIGURACIÓN DE RED Y CONECTIVIDAD ............................................................ 57
             5.7        VERIFICAR LA CONECTIVIDAD CIFS, NFS Y DDBOOST ................................................................ 59
             5.8        VERIFICAR EL ESTADO DEL FILE SYSTEM ....................................................................................... 60
             5.9        VERIFICAR EL ESTADO DE LA REPLICACIÓN ................................................................................... 61
             5.10       ACTUALIZAR LA CONFIGURACIÓN DE IPMI ...........

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0166

4 bytes from 172.18.228.3: icmp_seq=2 ttl=255 time=1.28 ms
                               ^C

                               --- 172.18.228.3 ping statistics ---
                               2 packets transmitted, 2 received, 0% packet loss, time 2ms
                               rtt min/avg/max/mdev = 1.225/1.253/1.282/0.045 ms
                               sysadmin@vdc-dd5# net ping 172.18.228.3 interface eth8bveth0
                               PING 172.18.228.3 (172.18.228.3) from 172.18.228.84 veth0: 56(84) bytes of data.
                               64 bytes from 172.18.228.3: icmp_seq=1 ttl=255 time=1.18 ms
                               64 bytes from 172.18.228.3: icmp_seq=2 ttl=255 time=5.11 ms
                               ^C

                               --- 172.18.228.3 ping statistics ---
                               2 packets transmitted, 2 received, 0% packet loss, time 2ms
                               rtt min/avg/max/mdev = 1.184/3.145/5.107/1.962 ms
                               sysadmin@vdc-dd5#




Controller upgrade
                                                               58/69
  Dell Customer Communication - Confidential




                     5.7 VERIFICAR LA CONECTIVIDAD CIFS, NFS Y DDBOOST
                          1. Revisar la conectividad CIFS.

                                  a. Si la autenticación estaba configurada con active-directory, chequear la
                                     conectividad con el dominio.

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0167

a. Si la autenticación estaba configurada con active-directory, chequear la
                                     conectividad con el dominio.

                                      cifs troubleshooting domaininfo


                                  b. Revisar la salida y, si el estado para “lsa-activedirectory-provider” es “unknown”
                                     hacer un “rejoin” al dominio.

                                      cifs set authentication active-directory realm


                                      Nota: si antes del “headswap” el sistema estaba en un “workgroup” se debe
                                      ejecutar previamente el comando “cifs reset authentication”.

                                  c. Verificar la conectividad CIFS. Habilitarlo, montar de nuevo los shares CIFS y
                                     verificando la operativa de los aplicativos de backup.

                                      cifs status
                                      cifs enable
                                      cifs show active


                          2. Revisar la conectividad NFS.

                                  a. Habilitar NFS, montar los shares NFS, y verificar la operativa de los aplicativos
                                     de backup.

                                      nfs status
                                      nfs enable
                                      nfs show clients


                          3. Revisar la conectivi

---
_Generated manually from indexed chunks. No background processing._

# VFMS v0 Grounded Output

**Query:** ddboost show connections

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0124

detener las operativas de los softwares de backup. Identificar
                             los sistemas utilizando

                              ddboost show connections


                          10. Determinar si la replicación está habilitada y deshabilitarla. No continuar hasta que la
                              replicación esté deshabilitada en todos los contextos.

                              replication status
                              replication disable all
                              replication status


                          11. Verificar que no hay tráfico en las tarjetas de red, ejecutarlo durante 60 segundos.

                              iostat 2


                          12. Verificar que no hay tráfico en los puertos FC.

                              scsitarget initiator show stats interval 2 count 60


                          13. Verificar las conexiones NFS, desmontar los file system en los servidores cliente y
                              deshabilitar NFS.




Controller upgrade
                                                               39/69
  Dell Customer Communication - Confidential




                              nfs show active
                              nfs disable
                               sysadmin@vdc-dd5# nfs show active
                               Path                                                         Client
                               ----------------------------------------------------------

---
_Generated manually from indexed chunks. No background processing._

---

## 5.8 VERIFICAR ESTADO DEL FILE SYSTEM
### Evidence
# VFMS v0 Grounded Output

**Query:** VERIFICAR EL ESTADO DEL FILE SYSTEM

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0005

5      ***CAMBIO DE CONTROLADORA .......................................................................................... 38
             5.1        APAGAR LA CONTROLADORA ORIGEN ............................................................................................ 38
             5.2        CAMBIO FÍSICO DE CONTROLADORA .............................................................................................. 42
             5.3        CONFIGURAR LA CONTROLADORA DE DESTINO ............................................................................. 44
             5.4        RECUPERAR Y VERIFICAR LA CONFIGURACIÓN SCSI TARGET ....................................................... 54
             5.5        VERIFICACIÓN DE LA CONFIGURACIÓN CLOUD TIER ..................................................................... 56
             5.6        VERIFICAR LA CONFIGURACIÓN DE RED Y CONECTIVIDAD ............................................................ 57
             5.7        VERIFICAR LA CONECTIVIDAD CIFS, NFS Y DDBOOST ................................................................ 59
             5.8        VERIFICAR EL ESTADO DEL FILE SYSTEM ....................................................................................... 60
             5.9        VERIFICAR EL ESTADO DE LA REPLICACIÓN ................................................................................... 61
             5.10       ACTUALIZAR LA CONFIGURACIÓN DE IPMI ...........

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0142

he old head, you will
                                    need to do one of the following after headswap completes:
                                    - unlock the filesystem          if you have encrypted data, or
                                    - set the system passphrase      if you don't have encrypted data

                                       Are you sure? (yes|no) [no]: yes

                               ok, proceeding.

                               Please enter sysadmin password to confirm 'system headswap':
                               Restoring the system configuration, do not power off / interrupt process ...

                               sysadmin@localhost#



                              Aunque la ejecución del comando “system headswap” tarde 30’, el proceso total de
                              “controller upgrade” puede durar hasta 8 o más horas.

                              Ejemplo:




                          6. Hacer “log in” en la controladora destino (9900) con la password de sysadmin de la
                             controladora original (9400).

                              Las password de todos los usuarios se migran con la ejecución de “system headswap”.

                          7. Verificar el estado del file system.




Controller upgrade
                                                               47/69
  Dell Customer Communication - Confidential




                              NO HABILITAR EL FILE SYSTEM en ese moment

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0168

nfs enable
                                      nfs show clients


                          3. Revisar la conectividad DDBoost.

                                      ddboost show user-name
                                      ddboost storage-unit show
                                      ddboost status
                                      ddboost fc status
                                      ddboost enable




Controller upgrade
                                                              59/69
  Dell Customer Communication - Confidential




                     5.8 VERIFICAR EL ESTADO DEL FILE SYSTEM
                     Verificar el file system, discos y sus enclosures.

                          1. Ejecutar los siguientes comandos y comparar la salida con la información previa al
                             “controller upgrade”.
                              disk show state
                              disk status
                              disk show hardware
                              system show ports
                              disk multipath status
                              filesys show space
                              enclosure show topology
                              replication show config


                          2. Revisar que la configuración de encriptación, snapshot y retention lock concuerda con la
                             original.

                              filesys encryption status

---
_Generated manually from indexed chunks. No background processing._

---

## 5.9 VERIFICAR ESTADO DE LA REPLICACIÓN
### Evidence
# VFMS v0 Grounded Output

**Query:** VERIFICAR EL ESTADO DE LA REPLICACIÓN

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0005

5      ***CAMBIO DE CONTROLADORA .......................................................................................... 38
             5.1        APAGAR LA CONTROLADORA ORIGEN ............................................................................................ 38
             5.2        CAMBIO FÍSICO DE CONTROLADORA .............................................................................................. 42
             5.3        CONFIGURAR LA CONTROLADORA DE DESTINO ............................................................................. 44
             5.4        RECUPERAR Y VERIFICAR LA CONFIGURACIÓN SCSI TARGET ....................................................... 54
             5.5        VERIFICACIÓN DE LA CONFIGURACIÓN CLOUD TIER ..................................................................... 56
             5.6        VERIFICAR LA CONFIGURACIÓN DE RED Y CONECTIVIDAD ............................................................ 57
             5.7        VERIFICAR LA CONECTIVIDAD CIFS, NFS Y DDBOOST ................................................................ 59
             5.8        VERIFICAR EL ESTADO DEL FILE SYSTEM ....................................................................................... 60
             5.9        VERIFICAR EL ESTADO DE LA REPLICACIÓN ................................................................................... 61
             5.10       ACTUALIZAR LA CONFIGURACIÓN DE IPMI ...........

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0169

iptación, snapshot y retention lock concuerda con la
                             original.

                              filesys encryption status
                              filesys encryption show
                              mtree list
                              mtree retention-lock status mtree mtree-path
                              snapshot list mtree mtree-path




Controller upgrade
                                                               60/69
  Dell Customer Communication - Confidential




                     5.9 VERIFICAR EL ESTADO DE LA REPLICACIÓN
             Verificar el estado de la replicación y reconfigurar en caso de que se haya cambiado el “hostname”.

                          1. Habilitar la replicación.

                              replication status
                              replication enable
                               sysadmin@vdc-dd5# replication status

                               **** This restorer is not configured for replication.

                               sysadmin@vdc-dd5#

                          2. Revisar que todos los contextos de réplica y su configuración se ha trasladado
                             correctamente.

                              replication show config


                                  a. En caso de cambio de “hostname” o IP, logarse en el sistema origen de réplica y
                                     modificar la configuración.

                                      replication

---
_Generated manually from indexed chunks. No background processing._

---

## 5.10 ACTUALIZAR CONFIGURACIÓN IPMI
### Evidence
# VFMS v0 Grounded Output

**Query:** ACTUALIZAR LA CONFIGURACIÓN DE IPMI

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0005

5      ***CAMBIO DE CONTROLADORA .......................................................................................... 38
             5.1        APAGAR LA CONTROLADORA ORIGEN ............................................................................................ 38
             5.2        CAMBIO FÍSICO DE CONTROLADORA .............................................................................................. 42
             5.3        CONFIGURAR LA CONTROLADORA DE DESTINO ............................................................................. 44
             5.4        RECUPERAR Y VERIFICAR LA CONFIGURACIÓN SCSI TARGET ....................................................... 54
             5.5        VERIFICACIÓN DE LA CONFIGURACIÓN CLOUD TIER ..................................................................... 56
             5.6        VERIFICAR LA CONFIGURACIÓN DE RED Y CONECTIVIDAD ............................................................ 57
             5.7        VERIFICAR LA CONECTIVIDAD CIFS, NFS Y DDBOOST ................................................................ 59
             5.8        VERIFICAR EL ESTADO DEL FILE SYSTEM ....................................................................................... 60
             5.9        VERIFICAR EL ESTADO DE LA REPLICACIÓN ................................................................................... 61
             5.10       ACTUALIZAR LA CONFIGURACIÓN DE IPMI ...........

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0006

........................................................................... 61
             5.10       ACTUALIZAR LA CONFIGURACIÓN DE IPMI ................................................................................... 62
             5.11       ACTUALIZACIÓN DE LICENCIAS ...................................................................................................... 64
             5.12       ACTUALIZAR REGISTRO EN EL ESRS GATEWAY ............................................................................ 66
             5.13       GENERAR EL AUTOSUPPORT........................................................................................................... 67
             6      AMPLIACIÓN DE ALMACENAMIENTO .................................................................................... 68




Controller upgrade
                                                                                   4/69
  Dell Customer Communication - Confidential




             2 INTRODUCCIÓN
             En el presente documento se aborda el proyecto de mejora del sistema Data Domain 9400 con número de
             serie CKM01210505504, bajo las siguientes premisas:

                 ➢ “Controller upgrade” a sistema Data Domain 9900 CRK00224110279.

                 ➢ Ampliación de capacidad de almacenamiento del sistema.

             A continuación, se indica el plan de acción a ejecutar.

                     2.1 PLAN DE ACCIÓN
             Se resumen los pasos a seguir:

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0170

en el sistema origen de réplica y
                                     modificar la configuración.

                                      replication modify <destination> connection-host <new-host-name> [port <port>]


                          3. Revisar que todos los contextos están habilitados y conectados.

                              replication status all




Controller upgrade
                                                               61/69
  Dell Customer Communication - Confidential




                     5.10 ACTUALIZAR LA CONFIGURACIÓN DE IPMI
                     La configuración de IPMI no se traslada durante el proceso de “controller upgrade”, actualizarla
                     con la información recogida.

                          1. Revisar la actual configuración.

                              ipmi show hardware
                              ipmi show config
                               sysadmin@vdc-dd5# ipmi show hardware
                               Firmware Revision: 5.10
                               IPMI Version     : 2.0
                               Manufacturer Name: DELL Inc.
                               Port    MAC Address          Link Status
                               -----   -----------------    -----------
                               bmc0a   b8:cb:29:f7:b6:ab    yes
                               -----   -----------------    -----------
                               sysadmin@vdc-dd5#

                          2. Config

---
_Generated manually from indexed chunks. No background processing._

# VFMS v0 Grounded Output

**Query:** user idrac create

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0145

storage add tier cache enclosure #
                               sysadmin@vdc-dd5# storage add tier cache enclosures 5

                               Checking storage requirements...done
                               Adding enclosure 5 to the cache tier...Enclosure 5 successfully added to the cache tier.

                               Updating system information...done

                               Successfully added: 5   done

                               sysadmin@vdc-dd5# storage show tier cache
                               Cache tier details:
                               Disk    Disks       Count  Disk       Additional
                               Group                      Size       Information
                               -----   --------    -----  --------   -----------
                               dg12    5.1-5.10    10     3.4 TiB
                               -----   --------    -----  --------   -----------

                               Current cache tier size: 34.9 TiB
                               sysadmin@vdc-dd5#

                          10. Para sistemas DD6900, DD9400 o DD9900 ejecutar lo siguiente para configurar y habilitar
                              “Retention Lock Compliance” y agregar los usuarios de iDRAC:

                              system retention-lock compliance configure
                              user idrac create
                              system retention-lock compliance enable

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0146

e configure
                              user idrac create
                              system retention-lock compliance enable


                              Reiniciar el sistema.

                              system reboot

                          11. Una vez finalizado el “upgrade”, habilitar el filesystem si está deshabilitado o en estado
                              “locked”.

                              system upgrade status
                              filesys status


                              filesys enable
                               sysadmin@vdc-dd5# system upgrade status
                               Current Upgrade Status: DD OS upgrade Succeeded
                               End time: 2023.07.11:14:38
                               sysadmin@vdc-dd5# filesys status
                               The filesystem is disabled and shutdown.
                               sysadmin@vdc-dd5# filesys enable
                               Please wait...............................
                               The filesystem is now enabled.
                               sysadmin@vdc-dd5#




Controller upgrade
                                                               49/69
  Dell Customer Communication - Confidential




                          12. Reconfigurar la red, en caso de ser necesario, de acuerdo con la información recogida
                              anteriormente de la controladora origen (9400) utilizando el comando “net config” o

---
_Generated manually from indexed chunks. No background processing._

# VFMS v0 Grounded Output

**Query:** retention-lock

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0027

-----   ----------   ---------   ------    ---------------   -
                               ---
                               1    CAPACITY-ACTIVE   HIGH_DENSITY   698.49 TiB   permanent   active    n/a
                               --   ---------------   ------------   ----------   ---------   ------    ---------------   -
                               ---
                               Licensed Active Tier capacity: 698.49 TiB*
                               * Depending on the hardware platform, usable filesystem capacities may vary.

                               Feature licenses:
                               ##   Feature                     Count   Type        State    Expiration Date   Note
                               --   -------------------------   -----   ---------   ------   ---------------   ----
                               1    REPLICATION                     1   permanent   active   n/a
                               2    VTL                             1   permanent   active   n/a
                               3    DDBOOST                         1   permanent   active   n/a
                               4    RETENTION-LOCK-GOVERNANCE       1   permanent   active   n/a
                               5    ENCRYPTION                      1   permanent   active   n/a
                               6    I/OS                            1   permanent   active   n/a
                               7    RETENTION-LOCK-COMPLIANCE       1   permanent   activ

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0028

I/OS                            1   permanent   active   n/a
                               7    RETENTION-LOCK-COMPLIANCE       1   permanent   active   n/a
                               --   -------------------------   -----   ---------   ------   ---------------   ----
                               License file last modified at : 2022/11/29 18:39:17.
                               DELLEMC@vdc-dd5#

                              Las licencias se migran correctamente, aunque se indicará un mismatch por que el
                              número de serie del Data Domain cambia y han de ser regularizadas en menos de 30
                              días.



                              TA-Origen-CKM012
                              10505504_DDOS_1000319364_16-Nov-2022.lic


                          10. Obtener la configuración de VTL.




Controller upgrade
                                                               17/69
  Dell Customer Communication - Confidential




                              OK, no.

                              vtl show config
                              vtl option show all
                               DELLEMC@vdc-dd5# vtl show config

                               VTL is not running.

                               DELLEMC@vdc-dd5#

                          11. Obtener la configuración de grupos de DDBoost FC.

                              OK, no.

                              ddboost fc group show detailed

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0044

cifs show config
                               DELLEMC@vdc-dd5# cifs share show
                               Shares information for: all shares

                               Shares displayed: 0
                               DELLEMC@vdc-dd5# cifs show config
                               Mode              Workgroup
                               Workgroup         not specified
                               WINS Server       not specified
                               NB Hostname       vdc-dd5
                               Max Connections   Not Available
                               Max Open Files    Not Available
                               DELLEMC@vdc-dd5#

                          17. Obtener la configuración de file system.

                              OK

                              Ejecutar para cada mtree los comandos “retention-lock status” and “snapshot list mtree”.

                              disk show state
                              disk status
                              disk show hardware
                              disk show reliability-data
                              system show ports
                              disk multipath status
                              filesys show space
                              enclosure show topology
                              filesys encryption show
                              mtree list
                              mtree retention-lock status mtree mtree-pa

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0045

filesys encryption show
                              mtree list
                              mtree retention-lock status mtree mtree-path




Controller upgrade
                                                                     21/69
  Dell Customer Communication - Confidential




                              snapshot list mtree mtree-path
                               DELLEMC@vdc-dd5# disk show state
                               Enclosure        Disk
                                 Row(disk-id)    1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16
                               --------------   -------------------------------------------------
                               1                 s . . . - - - - - - - . . . . .
                               2                |--------|--------|--------|--------|
                                                | Pack 1 | Pack 2 | Pack 3 | Pack 4 |
                                    E(49-60)    |. . s |. . s |. . s |. . s |
                                    D(37-48)    |. . . |. . . |. . . |. . . |
                                    C(25-36)    |. . . |. . . |. . . |. . . |
                                    B(13-24)    |. . . |. . . |. . . |. . . |
                                    A( 1-12)    |. . . |. . . |. . . |. . . |
                                                |--------|--------|--------|--------|
                               3                |--------|--------|--------|--------|

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0086

RW/Q
                               /data/col1/saphana_29348                   0.0 RW/Q
                               /data/col1/saphana_33392                   0.0 RW/Q
                               /data/col1/saphana_38020                1428.1 RW/Q
                               /data/col1/saphana_co5103                  0.0 RW/Q
                               /data/col1/saphana_co5104                  0.0 RW/Q
                               ----------------------------    -------------- ------
                                D    : Deleted
                                Q    : Quota Defined
                                RO   : Read Only
                                RW   : Read Write
                                RD   : Replication Destination
                                IRH : Retention-Lock Indefinite Retention Hold Enabled
                                ARL : Automatic-Retention-Lock Enabled
                                RLGE : Retention-Lock Governance Enabled
                                RLGD : Retention-Lock Governance Disabled
                                RLCE : Retention-Lock Compliance Enabled
                                M    : Mobile
                                m    : Migratable
                               DELLEMC@vdc-dd5#

                               DELLEMC@vdc-dd5# snapshot list all
                               Snapshots Summary:
                               -------------------

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0145

storage add tier cache enclosure #
                               sysadmin@vdc-dd5# storage add tier cache enclosures 5

                               Checking storage requirements...done
                               Adding enclosure 5 to the cache tier...Enclosure 5 successfully added to the cache tier.

                               Updating system information...done

                               Successfully added: 5   done

                               sysadmin@vdc-dd5# storage show tier cache
                               Cache tier details:
                               Disk    Disks       Count  Disk       Additional
                               Group                      Size       Information
                               -----   --------    -----  --------   -----------
                               dg12    5.1-5.10    10     3.4 TiB
                               -----   --------    -----  --------   -----------

                               Current cache tier size: 34.9 TiB
                               sysadmin@vdc-dd5#

                          10. Para sistemas DD6900, DD9400 o DD9900 ejecutar lo siguiente para configurar y habilitar
                              “Retention Lock Compliance” y agregar los usuarios de iDRAC:

                              system retention-lock compliance configure
                              user idrac create
                              system retention-lock compliance enable

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0146

e configure
                              user idrac create
                              system retention-lock compliance enable


                              Reiniciar el sistema.

                              system reboot

                          11. Una vez finalizado el “upgrade”, habilitar el filesystem si está deshabilitado o en estado
                              “locked”.

                              system upgrade status
                              filesys status


                              filesys enable
                               sysadmin@vdc-dd5# system upgrade status
                               Current Upgrade Status: DD OS upgrade Succeeded
                               End time: 2023.07.11:14:38
                               sysadmin@vdc-dd5# filesys status
                               The filesystem is disabled and shutdown.
                               sysadmin@vdc-dd5# filesys enable
                               Please wait...............................
                               The filesystem is now enabled.
                               sysadmin@vdc-dd5#




Controller upgrade
                                                               49/69
  Dell Customer Communication - Confidential




                          12. Reconfigurar la red, en caso de ser necesario, de acuerdo con la información recogida
                              anteriormente de la controladora origen (9400) utilizando el comando “net config” o

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0157

--   -------------------------   -----   ---------   -----   ---------------   -------------------
                               1    REPLICATION                     1   permanent   grace   n/a               Locking-id mismatch
                               2    VTL                             1   permanent   grace   n/a               Locking-id mismatch
                               3    DDBOOST                         1   permanent   grace   n/a               Locking-id mismatch
                               4    RETENTION-LOCK-GOVERNANCE       1   permanent   grace   n/a               Locking-id mismatch
                               5    ENCRYPTION                      1   permanent   grace   n/a               Locking-id mismatch
                               6    I/OS                            1   permanent   grace   n/a               Locking-id mismatch
                               7    RETENTION-LOCK-COMPLIANCE       1   permanent   grace   n/a               Locking-id mismatch
                               --   -------------------------   -----   ---------   -----   ---------------   -------------------
                               License file last modified at : 2022/11/29 18:39:17.
                               sysadmin@vdc-dd5#


                              Las licencias se han migrado correctamente, aunque se indica un mismatch por que
                              el número de serie del Data Domain cambia y han de ser regularizad

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0169

iptación, snapshot y retention lock concuerda con la
                             original.

                              filesys encryption status
                              filesys encryption show
                              mtree list
                              mtree retention-lock status mtree mtree-path
                              snapshot list mtree mtree-path




Controller upgrade
                                                               60/69
  Dell Customer Communication - Confidential




                     5.9 VERIFICAR EL ESTADO DE LA REPLICACIÓN
             Verificar el estado de la replicación y reconfigurar en caso de que se haya cambiado el “hostname”.

                          1. Habilitar la replicación.

                              replication status
                              replication enable
                               sysadmin@vdc-dd5# replication status

                               **** This restorer is not configured for replication.

                               sysadmin@vdc-dd5#

                          2. Revisar que todos los contextos de réplica y su configuración se ha trasladado
                             correctamente.

                              replication show config


                                  a. En caso de cambio de “hostname” o IP, logarse en el sistema origen de réplica y
                                     modificar la configuración.

                                      replication

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0174

-   ---------   -----   ---------------   ------------
                      -------
                      1    CAPACITY-ACTIVE   HIGH_DENSITY    698.49 TiB   permanent   grace   n/a               Locking-id
                      mismatch
                      --   ---------------   ------------   ----------   ---------   -----   ---------------   ------------
                      -------
                      Licensed Active Tier capacity: 698.49 TiB*
                      * Depending on the hardware platform, usable filesystem capacities may vary.

                      Feature licenses:
                      ##   Feature                     Count   Type        State    Expiration Date  Note
                      --   -------------------------    -----  ---------    -----   ---------------  -------------------
                      1    REPLICATION                      1  permanent    grace   n/a              Locking-id mismatch
                      2    VTL                              1  permanent   grace    n/a              Locking-id mismatch
                      3    DDBOOST                          1  permanent   grace    n/a              Locking-id mismatch
