# DD Controller Upgrade — STITCHED Runbook (VFMS v0)
**Scope:** Operator-friendly runbook assembled from VFMS grounded summaries.
**Source doc:** TA-ControllerUpgrade_Telefonica_DD9900.pdf
**Rule:** Do not invent steps. If missing, log it in GAPS and STOP.



---


## APPEND: summary__cambio_de_controladora.md

### VFMS v0 Grounded Output

**Query:** CAMBIO DE CONTROLADORA

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0004

3.7        INSTALAR DD-OS ........................................................................................................................... 10
             3.8        ***REVISAR COLOCACIÓN DE TARJETAS DE I/O ............................................................................ 11
             3.9        CONFIGURAR LAS INTERFACES IPMI Y ETHMB ............................................................................. 11
             3.10       OBTENER EL AUTOSUPPORT ........................................................................................................... 12
             3.11       ***REVISAR CARGA DE NVRAM................................................................................................... 12
             3.12       APAGAR CONTROLADORA .............................................................................................................. 12
             4      ***PREPARACIÓN DE LA CONTROLADORA ORIGEN (DD9400) ............................................ 14
             4.1        RECOGIDA DE INFORMACIÓN .......................................................................................................... 14
             4.2        ACTUALIZACIÓN DE DD-OS ........................................................................................................... 37
             5      ***CAMBIO DE CONTROLADORA .......................................................................................... 38
             5.1

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

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0121

ller upgrade
                                                                      37/69
  Dell Customer Communication - Confidential




             5 ***CAMBIO DE CONTROLADORA


                     5.1 APAGAR LA CONTROLADORA ORIGEN
                          1. Revisar que la ocupación del filesystem esté por debajo del 95% de ocupación.

                              filesystem show space
                               sysadmin@vdc-dd5# filesys show space

                               Active Tier:
                               Resource           Size GiB      Used GiB   Avail GiB     Use%   Cleanable GiB*
                               ----------------   --------    ----------   ---------     ----   --------------
                               /data: pre-comp           -    16149353.0           -        -                -
                               /data: post-comp   688292.9      468707.7    219585.2      68%          25292.8
                               /ddvar                 49.1          17.7        28.9      38%                -
                               /ddvar/core          1215.2           1.1      1152.4       0%                -
                               ----------------   --------    ----------   ---------     ----   --------------
                                * Estimated based

                          2. Detener todas las operativas de los softwares de backup sobre el Data Domain origen
                             (9400).

---
_Generated manually from indexed chunks. No background processing._


---


## APPEND: summary__apagar.md

### VFMS v0 Grounded Output

**Query:** APAGAR

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0004

3.7        INSTALAR DD-OS ........................................................................................................................... 10
             3.8        ***REVISAR COLOCACIÓN DE TARJETAS DE I/O ............................................................................ 11
             3.9        CONFIGURAR LAS INTERFACES IPMI Y ETHMB ............................................................................. 11
             3.10       OBTENER EL AUTOSUPPORT ........................................................................................................... 12
             3.11       ***REVISAR CARGA DE NVRAM................................................................................................... 12
             3.12       APAGAR CONTROLADORA .............................................................................................................. 12
             4      ***PREPARACIÓN DE LA CONTROLADORA ORIGEN (DD9400) ............................................ 14
             4.1        RECOGIDA DE INFORMACIÓN .......................................................................................................... 14
             4.2        ACTUALIZACIÓN DE DD-OS ........................................................................................................... 37
             5      ***CAMBIO DE CONTROLADORA .......................................................................................... 38
             5.1

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

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0019

NVRAM Batteries:
                               Card   Battery   Status  Charge     Charging  Time To      Temperature   Voltage
                                                                    Status    Full Charge
                               ----   -------   ------    ------    --------  -----------   -----------   -----
                       --
                               1      1         ok        96 %      enabled   4 mins        31 C          4.117
                       V
                               ----   -------   ------    ------    --------  -----------   -----------   -----
                       --
                       sysadmin@localhost#




                     3.12 APAGAR CONTROLADORA
                      Se deja encendida hasta el momento del ControllerUpgrade.

                      system poweroff




Controller upgrade
                                                             12/69
  Dell Customer Communication - Confidential




Controller upgrade
                                               13/69
  Dell Customer Communication - Confidential




             4 PREPARACIÓN DE LA CONTROLADORA ORIGEN (DD9400)
                     4.1 RECOGIDA DE INFORMACIÓN


             Los pasos que a continuación se indican deben ejecutarse al menos un día antes de la operativa de
             “controller upgrade”:

                 1. El Data Domain origen (DD9400) debe utilizar nombres de puerto tipo “slot-based”. En caso

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0121

ller upgrade
                                                                      37/69
  Dell Customer Communication - Confidential




             5 ***CAMBIO DE CONTROLADORA


                     5.1 APAGAR LA CONTROLADORA ORIGEN
                          1. Revisar que la ocupación del filesystem esté por debajo del 95% de ocupación.

                              filesystem show space
                               sysadmin@vdc-dd5# filesys show space

                               Active Tier:
                               Resource           Size GiB      Used GiB   Avail GiB     Use%   Cleanable GiB*
                               ----------------   --------    ----------   ---------     ----   --------------
                               /data: pre-comp           -    16149353.0           -        -                -
                               /data: post-comp   688292.9      468707.7    219585.2      68%          25292.8
                               /ddvar                 49.1          17.7        28.9      38%                -
                               /ddvar/core          1215.2           1.1      1152.4       0%                -
                               ----------------   --------    ----------   ---------     ----   --------------
                                * Estimated based

                          2. Detener todas las operativas de los softwares de backup sobre el Data Domain origen
                             (9400).

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0127

40/69
  Dell Customer Communication - Confidential




                               Removing disk 1.16...done

                               Updating system information...done

                               Disk 1.16 successfully removed.

                               sysadmin@vdc-dd5#
                               sysadmin@vdc-dd5#
                               sysadmin@vdc-dd5#
                               sysadmin@vdc-dd5# storage show tier cache

                               Storage addable disks:
                               Disk        Disks        Count    Disk       Enclosure    Shelf Capacity   Additional
                               Type                              Size       Model        License Needed   Information
                               ---------   ---------    -----    --------   ---------    --------------   -----------
                               (unknown)   1.12-1.16    5        3.4 TiB    DD9400       N/A
                               ---------   ---------    -----    --------   ---------    --------------   -----------
                               sysadmin@vdc-dd5#

                          17. Apagar la controladora origen, esperar a que todos los LEDS estén sin luz. No apagar las
                              bandejas.

                              system poweroff
                               sysadmin@vdc-dd5# system poweroff

                               The 'system poweroff' command shutdown

---
_Generated manually from indexed chunks. No background processing._


---


## APPEND: summary__cambio_físico.md

### VFMS v0 Grounded Output

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


## APPEND: summary__configurar_la_controladora_de_destino.md

### VFMS v0 Grounded Output

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


## APPEND: summary__recuperar_y_verificar_la_configuración_s.md

### VFMS v0 Grounded Output

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


---


## APPEND: summary__verificación_de_la_configuración_cloud_t.md

### VFMS v0 Grounded Output

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


---


## APPEND: summary__verificar_la_configuración_de_red.md

### VFMS v0 Grounded Output

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


## APPEND: summary__verificar_la_conectividad_cifs.md

### VFMS v0 Grounded Output

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


---


## APPEND: summary__verificar_el_estado_del_file_system.md

### VFMS v0 Grounded Output

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


## APPEND: summary__verificar_el_estado_de_la_replicación.md

### VFMS v0 Grounded Output

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


## APPEND: summary__actualizar_la_configuración_de_ipmi.md

### VFMS v0 Grounded Output

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


---


## APPEND (command-target): summary__filesys_show_space.md

### VFMS v0 Grounded Output

**Query:** filesys show space

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

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

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0080

b     Enet          10.0 Gbps    15.35.09        34:80:0d:bd:b3:5d (eth8b)
                               8c     Enet                       15.35.09        34:80:0d:bd:b3:5e (eth8c)
                               8d     Enet                       15.35.09        34:80:0d:bd:b3:5f (eth8d)
                               ----   ----------    ---------    ------------    -------------------------
                               DELLEMC@vdc-dd5# disk multipath status
                               Port   Hops   Status      Disk
                               ----   ----   -------     -----------------------------------
                               3a     1      Active      2.1 - 2.60
                                      2      Standby    3.1 - 3.60
                               3b     1      Active      4.1 - 4.6, 4.13 - 4.18, 4.25 - 4.30
                                      1      Standby    4.37 - 4.42, 4.49 - 4.54
                               7a     2      Standby     2.1 - 2.60
                                      1      Active     3.1 - 3.60
                               7b     1      Active      4.37 - 4.42, 4.49 - 4.54
                                      1      Standby    4.1 - 4.6, 4.13 - 4.18, 4.25 - 4.30
                               ----   ----   -------     -----------------------------------
                               DELLEMC@vdc-dd5# filesys show space

                               Active Tier:
                               Resource           Size G

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0081

DELLEMC@vdc-dd5# filesys show space

                               Active Tier:
                               Resource           Size GiB      Used GiB   Avail GiB    Use%   Cleanable GiB*




Controller upgrade
                                                                28/69
  Dell Customer Communication - Confidential




                               ----------------    --------      ----------   ---------    ----   --------------
                               /data: pre-comp             -     15390543.0            -      -                -
                               /data: post-comp    688292.9        432017.6     256275.3    63%           5967.2
                               /ddvar                   49.1           17.6         29.0    38%                -
                               /ddvar/core           1215.2             1.1       1152.4     0%                -
                               ----------------    --------      ----------   ---------    ----   --------------
                                 * Estimated based on last cleaning of 2023/06/02 09:43:05.
                               DELLEMC@vdc-dd5# enclosure show topology
                               Port        enc.ctrl.port          enc.ctrl.port
                               ----    -   -------------     -    -------------
                               3a      >    2.B.H: 2.B.E    >      3.B.H: 3.B.E
                               3b      >    4.B.H: 4.B.E

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0119

-----------------   ------------------
                                DELLEMC@vdc-dd5#




                          25. Para soportar el proceso de “controller upgrade” el filesystem del sistema origen ha de estar
                              por debajo del 95% de ocupación.

                              OK

                              filesystem show space
                                DELLEMC@vdc-dd5# filesys show space
                                Active Tier:
                                Resource           Size GiB     Used GiB   Avail GiB   Use%   Cleanable GiB*
                                ----------------   --------   ----------   ---------   ----   --------------
                                /data: pre-comp           -   16079747.0           -      -                -
                                /data: post-comp   688292.9     456889.6    231403.3    66%          24640.7
                                /ddvar                 49.1         17.6        29.0    38%                -
                                /ddvar/core          1215.2          1.1      1152.4     0%                -
                                ----------------   --------   ----------   ---------   ----   --------------
                                 * Estimated based on last cleaning of 2023/06/16 04:30:11.
                                sysadmin@vdc-dd5#




                      4.2 ACTUALIZACIÓN DE DD-OS
             Se debe instalar la misma versi

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0121

ller upgrade
                                                                      37/69
  Dell Customer Communication - Confidential




             5 ***CAMBIO DE CONTROLADORA


                     5.1 APAGAR LA CONTROLADORA ORIGEN
                          1. Revisar que la ocupación del filesystem esté por debajo del 95% de ocupación.

                              filesystem show space
                               sysadmin@vdc-dd5# filesys show space

                               Active Tier:
                               Resource           Size GiB      Used GiB   Avail GiB     Use%   Cleanable GiB*
                               ----------------   --------    ----------   ---------     ----   --------------
                               /data: pre-comp           -    16149353.0           -        -                -
                               /data: post-comp   688292.9      468707.7    219585.2      68%          25292.8
                               /ddvar                 49.1          17.7        28.9      38%                -
                               /ddvar/core          1215.2           1.1      1152.4       0%                -
                               ----------------   --------    ----------   ---------     ----   --------------
                                * Estimated based

                          2. Detener todas las operativas de los softwares de backup sobre el Data Domain origen
                             (9400).

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0153

255.255.255.252
                                  eth5b                 No            -     172.18.228.85    255.255.254.0
                                  eth8b                 No            -     172.18.228.86    255.255.254.0
                                  veth0                 No            -     172.18.228.84    255.255.254.0



                          13. Validar si los servicios NFS y CIFS se han habilitado al levantar el file system, y
                              habilitarles si es preciso.

                              NFS status
                              NFS enable
                              CIFS status
                              CIFS enable
                               sysadmin@vdc-dd5# nfs status

                               The NFS system is currently not active.

                               Total number of NFS requests handled = 12.
                               sysadmin@vdc-dd5# nfs enable
                               NFS server version(s) 3 enabled.

                               sysadmin@vdc-dd5# cifs status
                               CIFS is disabled.
                               sysadmin@vdc-dd5# cifs enable
                               The filesystem is enabled and running.
                               Starting CIFS access...
                               sysadmin@vdc-dd5#

                          14. Validar que es correcta la cantidad de espacio conectado.

                              filesys show space

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0154

-dd5#

                          14. Validar que es correcta la cantidad de espacio conectado.

                              filesys show space
                               sysadmin@vdc-dd5# filesys show space

                               Active Tier:
                               Resource           Size GiB     Used GiB   Avail GiB   Use%      Cleanable GiB*
                               ----------------   --------   ----------   ---------   ----      --------------
                               /data: pre-comp           -   16149354.0           -      -                   -
                               /data: post-comp   688285.6     468708.2    219577.5    68%             25292.8
                               /ddvar                 49.1          6.5        40.1    14%                   -
                               /ddvar/core          1215.2          0.1      1153.4     0%                   -
                               ----------------   --------   ----------   ---------   ----      --------------
                                * Estimated based on last cleaning of 2023/07/07 11:41:59.
                               sysadmin@vdc-dd5#

                          15. Si es necesario cambiar el “hostname” del sistema Data Domain hacerlo ahora. Se debe
                              tener en cuenta que algunas aplicaciones de backup no permiten el cambio de “hostname”.

                              net set hostname hostname


                          16. Si

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


## APPEND (command-target): summary__filesystem_show_space.md

### VFMS v0 Grounded Output

**Query:** filesystem show space

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0119

-----------------   ------------------
                                DELLEMC@vdc-dd5#




                          25. Para soportar el proceso de “controller upgrade” el filesystem del sistema origen ha de estar
                              por debajo del 95% de ocupación.

                              OK

                              filesystem show space
                                DELLEMC@vdc-dd5# filesys show space
                                Active Tier:
                                Resource           Size GiB     Used GiB   Avail GiB   Use%   Cleanable GiB*
                                ----------------   --------   ----------   ---------   ----   --------------
                                /data: pre-comp           -   16079747.0           -      -                -
                                /data: post-comp   688292.9     456889.6    231403.3    66%          24640.7
                                /ddvar                 49.1         17.6        29.0    38%                -
                                /ddvar/core          1215.2          1.1      1152.4     0%                -
                                ----------------   --------   ----------   ---------   ----   --------------
                                 * Estimated based on last cleaning of 2023/06/16 04:30:11.
                                sysadmin@vdc-dd5#




                      4.2 ACTUALIZACIÓN DE DD-OS
             Se debe instalar la misma versi

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0121

ller upgrade
                                                                      37/69
  Dell Customer Communication - Confidential




             5 ***CAMBIO DE CONTROLADORA


                     5.1 APAGAR LA CONTROLADORA ORIGEN
                          1. Revisar que la ocupación del filesystem esté por debajo del 95% de ocupación.

                              filesystem show space
                               sysadmin@vdc-dd5# filesys show space

                               Active Tier:
                               Resource           Size GiB      Used GiB   Avail GiB     Use%   Cleanable GiB*
                               ----------------   --------    ----------   ---------     ----   --------------
                               /data: pre-comp           -    16149353.0           -        -                -
                               /data: post-comp   688292.9      468707.7    219585.2      68%          25292.8
                               /ddvar                 49.1          17.7        28.9      38%                -
                               /ddvar/core          1215.2           1.1      1152.4       0%                -
                               ----------------   --------    ----------   ---------     ----   --------------
                                * Estimated based

                          2. Detener todas las operativas de los softwares de backup sobre el Data Domain origen
                             (9400).

---
_Generated manually from indexed chunks. No background processing._


---


## APPEND (command-target): summary__system_poweroff.md

### VFMS v0 Grounded Output

**Query:** system poweroff

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0019

NVRAM Batteries:
                               Card   Battery   Status  Charge     Charging  Time To      Temperature   Voltage
                                                                    Status    Full Charge
                               ----   -------   ------    ------    --------  -----------   -----------   -----
                       --
                               1      1         ok        96 %      enabled   4 mins        31 C          4.117
                       V
                               ----   -------   ------    ------    --------  -----------   -----------   -----
                       --
                       sysadmin@localhost#




                     3.12 APAGAR CONTROLADORA
                      Se deja encendida hasta el momento del ControllerUpgrade.

                      system poweroff




Controller upgrade
                                                             12/69
  Dell Customer Communication - Confidential




Controller upgrade
                                               13/69
  Dell Customer Communication - Confidential




             4 PREPARACIÓN DE LA CONTROLADORA ORIGEN (DD9400)
                     4.1 RECOGIDA DE INFORMACIÓN


             Los pasos que a continuación se indican deben ejecutarse al menos un día antes de la operativa de
             “controller upgrade”:

                 1. El Data Domain origen (DD9400) debe utilizar nombres de puerto tipo “slot-based”. En caso

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0127

40/69
  Dell Customer Communication - Confidential




                               Removing disk 1.16...done

                               Updating system information...done

                               Disk 1.16 successfully removed.

                               sysadmin@vdc-dd5#
                               sysadmin@vdc-dd5#
                               sysadmin@vdc-dd5#
                               sysadmin@vdc-dd5# storage show tier cache

                               Storage addable disks:
                               Disk        Disks        Count    Disk       Enclosure    Shelf Capacity   Additional
                               Type                              Size       Model        License Needed   Information
                               ---------   ---------    -----    --------   ---------    --------------   -----------
                               (unknown)   1.12-1.16    5        3.4 TiB    DD9400       N/A
                               ---------   ---------    -----    --------   ---------    --------------   -----------
                               sysadmin@vdc-dd5#

                          17. Apagar la controladora origen, esperar a que todos los LEDS estén sin luz. No apagar las
                              bandejas.

                              system poweroff
                               sysadmin@vdc-dd5# system poweroff

                               The 'system poweroff' command shutdown

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


## APPEND (command-target): summary__ddboost_show_connections.md

### VFMS v0 Grounded Output

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


## APPEND (command-target): summary__data-movement_status.md

### VFMS v0 Grounded Output

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


---


## APPEND (command-target): summary__data-movement_stop.md

### VFMS v0 Grounded Output

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


## APPEND (command-target): summary__scsitarget.md

### VFMS v0 Grounded Output

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


                                       *Configuración en controladora origen (DD9400)
                                         Endpoint        WWPN             WWNN     Source Port     Destination Port




                                  f.   Habilitar los endpoints.

                                       scsitarget endpoint enable all




Controller upgrade
                                                                  55/69
  Dell Customer Communication - Confidential




                          5. Conectar los cables FC SAN.

                          6. Verificar que todos los dispositivos son visibles en el grupo con los nuevos puertos.

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


## APPEND (command-target): summary__vtl_group_show.md

### VFMS v0 Grounded Output

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


## APPEND (command-target): summary__user_idrac_create.md

### VFMS v0 Grounded Output

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


---


## APPEND (command-target): summary__retention-lock.md

### VFMS v0 Grounded Output

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
                      4    RETENTION-LOCK-GOVERNANCE        1  permanent   grace    n/a              Locking-id mismatch
                      5    ENCRYPTION                       1  permanent   grace    n/a              Locking-id mismatch
                      6    I/OS                             1  permane

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0175

1  permanent   grace    n/a              Locking-id mismatch
                      6    I/OS                             1  permanent   grace    n/a              Locking-id mismatch
                      7    RETENTION-LOCK-COMPLIANCE        1  permanent   grace    n/a              Locking-id mismatch
                      --   -------------------------    -----  ---------    -----   ---------------  -------------------
                      License file last modified at : 2022/11/29 18:39:17.
                      sysadmin@vdc-dd5# elicense update
                      Enter the content of license file and then press Control-D, or press Control-C to cancel.
                      #############################################################
                      # EMC License File
                      # Activation Date: Jul 10, 2023 08:22:43 AM
                      # Activated By: Abdul Samad
                      # Type:UNSERVED
                      #############################################################
                      INCREMENT DD_REPLICATION EMCLM 1 permanent uncounted \
                               VENDOR_STRING="LOCKING_ID=CRK00224110279;CAPACITY=960;PRODUCT_LINE=Data \
                               Domain OS;FEATURE_NAME=REPLICATION;UOM_CODE=CB;UOM_NAME=Raw \
                               Capacity in TB;PLC=DDOS" HOSTID=ANY dist_info="ACTIVATED TO \
                               TELEFÓNICA CYBERSECURITY AND CLOUD TECH S.L." ISSUER

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0176

Capacity in TB;PLC=DDOS" HOSTID=ANY dist_info="ACTIVATED TO \
                               TELEFÓNICA CYBERSECURITY AND CLOUD TECH S.L." ISSUER=EMC \
                               ISSUED=10-Jul-2023 NOTICE="ACTIVATED TO License Site Number: \
                               1005820526" SN=1000541220 SIGN="00DF E023 AA84 5C08 0C39 9317 \
                               8F01 5000 0A00 1172 C6B4 E5D5 E1CD F6E2 2570"
                      INCREMENT DD_I_OS EMCLM 1.0 permanent uncounted \
                               VENDOR_STRING="LOCKING_ID=CRK00224110279;PRODUCT_LINE=Data \
                               Domain OS;FEATURE_NAME=I/OS;UOM_CODE=IA;UOM_NAME=Instance per \
                               Server;PLC=DDOS" HOSTID=ANY dist_info="ACTIVATED TO \
                               TELEFÓNICA CYBERSECURITY AND CLOUD TECH S.L." ISSUER=EMC \
                               ISSUED=10-Jul-2023 NOTICE="ACTIVATED TO License Site Number: \
                               1005820526" SN=1000541220 SIGN="00AA 48CA FC78 2BAA 9F2F 87F3 \
                               8198 5900 CA62 6D8F A2E2 2500 5E69 9D5D 7019"
                      INCREMENT DD_RETENTION_LOCK_GOVERNANCE EMCLM 1 permanent uncounted \
                               VENDOR_STRING="LOCKING_ID=CRK00224110279;PRODUCT_LINE=Data \
                               Domain \
                               OS;FEATURE_NAME=RETENTION-LOCK-GOVERNANCE;UOM_CODE=IA;UOM_NAME=Instance \
                               per Server;PLC=DDO

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0177

OS;FEATURE_NAME=RETENTION-LOCK-GOVERNANCE;UOM_CODE=IA;UOM_NAME=Instance \
                               per Server;PLC=DDOS" HOSTID=ANY dist_info="ACTIVATED TO \
                               TELEFÓNICA CYBERSECURITY AND CLOUD TECH S.L." ISSUER=EMC \
                               ISSUED=10-Jul-2023 NOTICE="ACTIVATED TO License Site Number: \




Controller upgrade
                                                                64/69
  Dell Customer Communication - Confidential




                               1005820526" SN=1000541220 SIGN="0068 5AC2 CC7C 0B30 E67B 999A \
                               D016 4600 23AA 6E8D 00EB C00D E370 9CFE 661B"
                      INCREMENT DD_ENCRYPTION EMCLM 1.0 permanent uncounted \
                               VENDOR_STRING="LOCKING_ID=CRK00224110279;PRODUCT_LINE=Data \
                               Domain \
                               OS;FEATURE_NAME=ENCRYPTION;UOM_CODE=IA;UOM_NAME=Instance per \
                               Server;PLC=DDOS" HOSTID=ANY dist_info="ACTIVATED TO \
                               TELEFÓNICA CYBERSECURITY AND CLOUD TECH S.L." ISSUER=EMC \
                               ISSUED=10-Jul-2023 NOTICE="ACTIVATED TO License Site Number: \
                               1005820526" SN=1000541220 SIGN="0089 5AFE 7293 9811 1285 B729 \
                               D378 5700 20FC 29F0 2FAA 17F3 3D82 F367 57B0"
                      INCREMENT DD_DDBOOST EMCLM 1.0 permanent unc

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0179

S.L." ISSUER=EMC \
                               ISSUED=10-Jul-2023 NOTICE="ACTIVATED TO License Site Number: \
                               1005820526" SN=1000541220 SIGN="000B E413 D549 5594 56B2 970E \
                               E6FD 9C00 3285 0CA6 C261 89C3 837F 1E70 FCBA"
                      INCREMENT DD_VTL EMCLM 1.0 permanent uncounted \
                               VENDOR_STRING="LOCKING_ID=CRK00224110279;PRODUCT_LINE=Data \
                               Domain OS;FEATURE_NAME=VTL;UOM_CODE=IA;UOM_NAME=Instance per \
                               Server;PLC=DDOS" HOSTID=ANY dist_info="ACTIVATED TO \
                               TELEFÓNICA CYBERSECURITY AND CLOUD TECH S.L." ISSUER=EMC \
                               ISSUED=10-Jul-2023 NOTICE="ACTIVATED TO License Site Number: \
                               1005820526" SN=1000541220 SIGN="0076 BFBD FBEF 683A C782 4EAE \
                               9D27 8500 841C EFFD E216 431B B24B 26DC BBEF"
                      INCREMENT DD_RETENTION_LOCK_COMPLIANCE EMCLM 1.0 permanent uncounted \
                               VENDOR_STRING="LOCKING_ID=CRK00224110279;PRODUCT_LINE=Data \
                               Domain \
                               OS;FEATURE_NAME=RETENTION-LOCK-COMPLIANCE;UOM_CODE=IA;UOM_NAME=Instance \
                               per Server;PLC=DDOS" HOSTID=ANY dist_info="ACTIVATED TO \
                               TELEFÓNICA CYBERSECURITY AND CLOUD TECH S.L." ISSUER=EMC \

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0181

State   Expiration Date    Note
                      --   -------------------------   -----   ---------   -----   ---------------    -------------------
                      1    REPLICATION                     1   permanent   grace   n/a                Locking-id mismatch
                      2    VTL                             1   permanent   grace   n/a                Locking-id mismatch
                      3    DDBOOST                         1   permanent   grace   n/a                Locking-id mismatch
                      4    RETENTION-LOCK-GOVERNANCE       1   permanent   grace   n/a                Locking-id mismatch
                      5    ENCRYPTION                      1   permanent   grace   n/a                Locking-id mismatch
                      6    I/OS                            1   permanent   grace   n/a                Locking-id mismatch
                      7    RETENTION-LOCK-COMPLIANCE       1   permanent   grace   n/a                Locking-id mismatch
                      --   -------------------------   -----   ---------   -----   ---------------    -------------------

                      New licenses:

                      Capacity licenses:
                      ##   Feature           Shelf Model    Capacity     Type        State    Expiration Date   Note
                      --   ---------------   ------------   ----------   ---------   ------   ---------------   ----
                      1    CAPACITY-ACTIVE   HIGH_DEN

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0182

--   ---------------   ------------   ----------   ---------   ------   ---------------   ----
                      1    CAPACITY-ACTIVE   HIGH_DENSITY   785.80 TiB   permanent   active   n/a
                      --   ---------------   ------------   ----------   ---------   ------   ---------------    ----
                      Licensed Active Tier capacity: 785.80 TiB*
                      * Depending on the hardware platform, usable filesystem capacities may vary.

                      Feature licenses:
                      ##   Feature                     Count   Type        State    Expiration Date   Note




Controller upgrade
                                                                65/69
  Dell Customer Communication - Confidential




                      --   -------------------------   -----   ---------   ------   ---------------      ----
                      1    REPLICATION                     1   permanent   active   n/a
                      2    I/OS                            1   permanent   active   n/a
                      3    RETENTION-LOCK-GOVERNANCE       1   permanent   active   n/a
                      4    ENCRYPTION                      1   permanent   active   n/a
                      5    DDBOOST                         1   permanent   active   n/a
                      6    VTL                             1   permanent   active   n/a
                      7    RETENTION-LOCK-COMPLIANCE       1   permanent   active   n/a

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0183

1   permanent   active   n/a
                      7    RETENTION-LOCK-COMPLIANCE       1   permanent   active   n/a
                      --   -------------------------   -----   ---------   ------   ---------------      ----

                      ** New license(s) will overwrite all existing license(s).

                      Do you want to proceed? (yes|no) [yes]: yes


                      eLicense(s) updated.
                      sysadmin@vdc-dd5#
                      sysadmin@vdc-dd5# alerts show current
                      No active alerts.
                      sysadmin@vdc-dd5# elicense show
                      System locking-id: CRK00224110279

                      Licensing scheme: EMC Electronic License Management System (ELMS) node-locked mode

                      Capacity licenses:
                      ##   Feature           Shelf Model    Capacity     Type        State    Expiration Date   Note
                      --   ---------------   ------------   ----------   ---------   ------   ---------------   ----
                      1    CAPACITY-ACTIVE   HIGH_DENSITY   785.80 TiB   permanent   active   n/a
                      --   ---------------   ------------   ----------   ---------   ------   ---------------   ----
                      Licensed Active Tier capacity: 785.80 TiB*
                      * Depending on the hardware platform, usable filesystem capacities may vary.

                      Feature licenses:

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0184

.80 TiB*
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
                      7    RETENTION-LOCK-COMPLIANCE       1   permanent   active   n/a
                      --   -------------------------   -----   ---------   ------   ---------------      ----
                      License file last modified at : 2023/07/11 15:49:42.
                      sysadmin@vdc-dd5# date
                      Tue Jul 11 15:50:01 CEST 2023
                      sysadmin@vdc-dd5#




                     5.12 ACTUALIZAR REGISTRO EN EL ESRS GATEWAY
                     Actualizar el registro en el ESRS Gateway para reflejar el nuevo número de serie del sistema.

---
_Generated manually from indexed chunks. No background processing._


---


## APPEND (command-target): summary__filesys_show_space.md

### VFMS v0 Grounded Output

**Query:** filesys show space

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

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

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0080

b     Enet          10.0 Gbps    15.35.09        34:80:0d:bd:b3:5d (eth8b)
                               8c     Enet                       15.35.09        34:80:0d:bd:b3:5e (eth8c)
                               8d     Enet                       15.35.09        34:80:0d:bd:b3:5f (eth8d)
                               ----   ----------    ---------    ------------    -------------------------
                               DELLEMC@vdc-dd5# disk multipath status
                               Port   Hops   Status      Disk
                               ----   ----   -------     -----------------------------------
                               3a     1      Active      2.1 - 2.60
                                      2      Standby    3.1 - 3.60
                               3b     1      Active      4.1 - 4.6, 4.13 - 4.18, 4.25 - 4.30
                                      1      Standby    4.37 - 4.42, 4.49 - 4.54
                               7a     2      Standby     2.1 - 2.60
                                      1      Active     3.1 - 3.60
                               7b     1      Active      4.37 - 4.42, 4.49 - 4.54
                                      1      Standby    4.1 - 4.6, 4.13 - 4.18, 4.25 - 4.30
                               ----   ----   -------     -----------------------------------
                               DELLEMC@vdc-dd5# filesys show space

                               Active Tier:
                               Resource           Size G

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0081

DELLEMC@vdc-dd5# filesys show space

                               Active Tier:
                               Resource           Size GiB      Used GiB   Avail GiB    Use%   Cleanable GiB*




Controller upgrade
                                                                28/69
  Dell Customer Communication - Confidential




                               ----------------    --------      ----------   ---------    ----   --------------
                               /data: pre-comp             -     15390543.0            -      -                -
                               /data: post-comp    688292.9        432017.6     256275.3    63%           5967.2
                               /ddvar                   49.1           17.6         29.0    38%                -
                               /ddvar/core           1215.2             1.1       1152.4     0%                -
                               ----------------    --------      ----------   ---------    ----   --------------
                                 * Estimated based on last cleaning of 2023/06/02 09:43:05.
                               DELLEMC@vdc-dd5# enclosure show topology
                               Port        enc.ctrl.port          enc.ctrl.port
                               ----    -   -------------     -    -------------
                               3a      >    2.B.H: 2.B.E    >      3.B.H: 3.B.E
                               3b      >    4.B.H: 4.B.E

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0119

-----------------   ------------------
                                DELLEMC@vdc-dd5#




                          25. Para soportar el proceso de “controller upgrade” el filesystem del sistema origen ha de estar
                              por debajo del 95% de ocupación.

                              OK

                              filesystem show space
                                DELLEMC@vdc-dd5# filesys show space
                                Active Tier:
                                Resource           Size GiB     Used GiB   Avail GiB   Use%   Cleanable GiB*
                                ----------------   --------   ----------   ---------   ----   --------------
                                /data: pre-comp           -   16079747.0           -      -                -
                                /data: post-comp   688292.9     456889.6    231403.3    66%          24640.7
                                /ddvar                 49.1         17.6        29.0    38%                -
                                /ddvar/core          1215.2          1.1      1152.4     0%                -
                                ----------------   --------   ----------   ---------   ----   --------------
                                 * Estimated based on last cleaning of 2023/06/16 04:30:11.
                                sysadmin@vdc-dd5#




                      4.2 ACTUALIZACIÓN DE DD-OS
             Se debe instalar la misma versi

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0121

ller upgrade
                                                                      37/69
  Dell Customer Communication - Confidential




             5 ***CAMBIO DE CONTROLADORA


                     5.1 APAGAR LA CONTROLADORA ORIGEN
                          1. Revisar que la ocupación del filesystem esté por debajo del 95% de ocupación.

                              filesystem show space
                               sysadmin@vdc-dd5# filesys show space

                               Active Tier:
                               Resource           Size GiB      Used GiB   Avail GiB     Use%   Cleanable GiB*
                               ----------------   --------    ----------   ---------     ----   --------------
                               /data: pre-comp           -    16149353.0           -        -                -
                               /data: post-comp   688292.9      468707.7    219585.2      68%          25292.8
                               /ddvar                 49.1          17.7        28.9      38%                -
                               /ddvar/core          1215.2           1.1      1152.4       0%                -
                               ----------------   --------    ----------   ---------     ----   --------------
                                * Estimated based

                          2. Detener todas las operativas de los softwares de backup sobre el Data Domain origen
                             (9400).

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0153

255.255.255.252
                                  eth5b                 No            -     172.18.228.85    255.255.254.0
                                  eth8b                 No            -     172.18.228.86    255.255.254.0
                                  veth0                 No            -     172.18.228.84    255.255.254.0



                          13. Validar si los servicios NFS y CIFS se han habilitado al levantar el file system, y
                              habilitarles si es preciso.

                              NFS status
                              NFS enable
                              CIFS status
                              CIFS enable
                               sysadmin@vdc-dd5# nfs status

                               The NFS system is currently not active.

                               Total number of NFS requests handled = 12.
                               sysadmin@vdc-dd5# nfs enable
                               NFS server version(s) 3 enabled.

                               sysadmin@vdc-dd5# cifs status
                               CIFS is disabled.
                               sysadmin@vdc-dd5# cifs enable
                               The filesystem is enabled and running.
                               Starting CIFS access...
                               sysadmin@vdc-dd5#

                          14. Validar que es correcta la cantidad de espacio conectado.

                              filesys show space

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0154

-dd5#

                          14. Validar que es correcta la cantidad de espacio conectado.

                              filesys show space
                               sysadmin@vdc-dd5# filesys show space

                               Active Tier:
                               Resource           Size GiB     Used GiB   Avail GiB   Use%      Cleanable GiB*
                               ----------------   --------   ----------   ---------   ----      --------------
                               /data: pre-comp           -   16149354.0           -      -                   -
                               /data: post-comp   688285.6     468708.2    219577.5    68%             25292.8
                               /ddvar                 49.1          6.5        40.1    14%                   -
                               /ddvar/core          1215.2          0.1      1153.4     0%                   -
                               ----------------   --------   ----------   ---------   ----      --------------
                                * Estimated based on last cleaning of 2023/07/07 11:41:59.
                               sysadmin@vdc-dd5#

                          15. Si es necesario cambiar el “hostname” del sistema Data Domain hacerlo ahora. Se debe
                              tener en cuenta que algunas aplicaciones de backup no permiten el cambio de “hostname”.

                              net set hostname hostname


                          16. Si

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


## APPEND (command-target): summary__filesystem_show_space.md

### VFMS v0 Grounded Output

**Query:** filesystem show space

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0119

-----------------   ------------------
                                DELLEMC@vdc-dd5#




                          25. Para soportar el proceso de “controller upgrade” el filesystem del sistema origen ha de estar
                              por debajo del 95% de ocupación.

                              OK

                              filesystem show space
                                DELLEMC@vdc-dd5# filesys show space
                                Active Tier:
                                Resource           Size GiB     Used GiB   Avail GiB   Use%   Cleanable GiB*
                                ----------------   --------   ----------   ---------   ----   --------------
                                /data: pre-comp           -   16079747.0           -      -                -
                                /data: post-comp   688292.9     456889.6    231403.3    66%          24640.7
                                /ddvar                 49.1         17.6        29.0    38%                -
                                /ddvar/core          1215.2          1.1      1152.4     0%                -
                                ----------------   --------   ----------   ---------   ----   --------------
                                 * Estimated based on last cleaning of 2023/06/16 04:30:11.
                                sysadmin@vdc-dd5#




                      4.2 ACTUALIZACIÓN DE DD-OS
             Se debe instalar la misma versi

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0121

ller upgrade
                                                                      37/69
  Dell Customer Communication - Confidential




             5 ***CAMBIO DE CONTROLADORA


                     5.1 APAGAR LA CONTROLADORA ORIGEN
                          1. Revisar que la ocupación del filesystem esté por debajo del 95% de ocupación.

                              filesystem show space
                               sysadmin@vdc-dd5# filesys show space

                               Active Tier:
                               Resource           Size GiB      Used GiB   Avail GiB     Use%   Cleanable GiB*
                               ----------------   --------    ----------   ---------     ----   --------------
                               /data: pre-comp           -    16149353.0           -        -                -
                               /data: post-comp   688292.9      468707.7    219585.2      68%          25292.8
                               /ddvar                 49.1          17.7        28.9      38%                -
                               /ddvar/core          1215.2           1.1      1152.4       0%                -
                               ----------------   --------    ----------   ---------     ----   --------------
                                * Estimated based

                          2. Detener todas las operativas de los softwares de backup sobre el Data Domain origen
                             (9400).

---
_Generated manually from indexed chunks. No background processing._


---


## APPEND (command-target): summary__ddboost_show_connections.md

### VFMS v0 Grounded Output

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


## APPEND (command-target): summary__data-movement_status.md

### VFMS v0 Grounded Output

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


---


## APPEND (command-target): summary__data-movement_stop.md

### VFMS v0 Grounded Output

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


## APPEND (command-target): summary__scsitarget.md

### VFMS v0 Grounded Output

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


                                       *Configuración en controladora origen (DD9400)
                                         Endpoint        WWPN             WWNN     Source Port     Destination Port




                                  f.   Habilitar los endpoints.

                                       scsitarget endpoint enable all




Controller upgrade
                                                                  55/69
  Dell Customer Communication - Confidential




                          5. Conectar los cables FC SAN.

                          6. Verificar que todos los dispositivos son visibles en el grupo con los nuevos puertos.

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


## APPEND (command-target): summary__vtl_group_show.md

### VFMS v0 Grounded Output

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


## APPEND (command-target): summary__system_poweroff.md

### VFMS v0 Grounded Output

**Query:** system poweroff

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0019

NVRAM Batteries:
                               Card   Battery   Status  Charge     Charging  Time To      Temperature   Voltage
                                                                    Status    Full Charge
                               ----   -------   ------    ------    --------  -----------   -----------   -----
                       --
                               1      1         ok        96 %      enabled   4 mins        31 C          4.117
                       V
                               ----   -------   ------    ------    --------  -----------   -----------   -----
                       --
                       sysadmin@localhost#




                     3.12 APAGAR CONTROLADORA
                      Se deja encendida hasta el momento del ControllerUpgrade.

                      system poweroff




Controller upgrade
                                                             12/69
  Dell Customer Communication - Confidential




Controller upgrade
                                               13/69
  Dell Customer Communication - Confidential




             4 PREPARACIÓN DE LA CONTROLADORA ORIGEN (DD9400)
                     4.1 RECOGIDA DE INFORMACIÓN


             Los pasos que a continuación se indican deben ejecutarse al menos un día antes de la operativa de
             “controller upgrade”:

                 1. El Data Domain origen (DD9400) debe utilizar nombres de puerto tipo “slot-based”. En caso

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0127

40/69
  Dell Customer Communication - Confidential




                               Removing disk 1.16...done

                               Updating system information...done

                               Disk 1.16 successfully removed.

                               sysadmin@vdc-dd5#
                               sysadmin@vdc-dd5#
                               sysadmin@vdc-dd5#
                               sysadmin@vdc-dd5# storage show tier cache

                               Storage addable disks:
                               Disk        Disks        Count    Disk       Enclosure    Shelf Capacity   Additional
                               Type                              Size       Model        License Needed   Information
                               ---------   ---------    -----    --------   ---------    --------------   -----------
                               (unknown)   1.12-1.16    5        3.4 TiB    DD9400       N/A
                               ---------   ---------    -----    --------   ---------    --------------   -----------
                               sysadmin@vdc-dd5#

                          17. Apagar la controladora origen, esperar a que todos los LEDS estén sin luz. No apagar las
                              bandejas.

                              system poweroff
                               sysadmin@vdc-dd5# system poweroff

                               The 'system poweroff' command shutdown

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


## APPEND (command-target): summary__user_idrac_create.md

### VFMS v0 Grounded Output

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


---


## APPEND (command-target): summary__retention-lock.md

### VFMS v0 Grounded Output

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
                      4    RETENTION-LOCK-GOVERNANCE        1  permanent   grace    n/a              Locking-id mismatch
                      5    ENCRYPTION                       1  permanent   grace    n/a              Locking-id mismatch
                      6    I/OS                             1  permane

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0175

1  permanent   grace    n/a              Locking-id mismatch
                      6    I/OS                             1  permanent   grace    n/a              Locking-id mismatch
                      7    RETENTION-LOCK-COMPLIANCE        1  permanent   grace    n/a              Locking-id mismatch
                      --   -------------------------    -----  ---------    -----   ---------------  -------------------
                      License file last modified at : 2022/11/29 18:39:17.
                      sysadmin@vdc-dd5# elicense update
                      Enter the content of license file and then press Control-D, or press Control-C to cancel.
                      #############################################################
                      # EMC License File
                      # Activation Date: Jul 10, 2023 08:22:43 AM
                      # Activated By: Abdul Samad
                      # Type:UNSERVED
                      #############################################################
                      INCREMENT DD_REPLICATION EMCLM 1 permanent uncounted \
                               VENDOR_STRING="LOCKING_ID=CRK00224110279;CAPACITY=960;PRODUCT_LINE=Data \
                               Domain OS;FEATURE_NAME=REPLICATION;UOM_CODE=CB;UOM_NAME=Raw \
                               Capacity in TB;PLC=DDOS" HOSTID=ANY dist_info="ACTIVATED TO \
                               TELEFÓNICA CYBERSECURITY AND CLOUD TECH S.L." ISSUER

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0176

Capacity in TB;PLC=DDOS" HOSTID=ANY dist_info="ACTIVATED TO \
                               TELEFÓNICA CYBERSECURITY AND CLOUD TECH S.L." ISSUER=EMC \
                               ISSUED=10-Jul-2023 NOTICE="ACTIVATED TO License Site Number: \
                               1005820526" SN=1000541220 SIGN="00DF E023 AA84 5C08 0C39 9317 \
                               8F01 5000 0A00 1172 C6B4 E5D5 E1CD F6E2 2570"
                      INCREMENT DD_I_OS EMCLM 1.0 permanent uncounted \
                               VENDOR_STRING="LOCKING_ID=CRK00224110279;PRODUCT_LINE=Data \
                               Domain OS;FEATURE_NAME=I/OS;UOM_CODE=IA;UOM_NAME=Instance per \
                               Server;PLC=DDOS" HOSTID=ANY dist_info="ACTIVATED TO \
                               TELEFÓNICA CYBERSECURITY AND CLOUD TECH S.L." ISSUER=EMC \
                               ISSUED=10-Jul-2023 NOTICE="ACTIVATED TO License Site Number: \
                               1005820526" SN=1000541220 SIGN="00AA 48CA FC78 2BAA 9F2F 87F3 \
                               8198 5900 CA62 6D8F A2E2 2500 5E69 9D5D 7019"
                      INCREMENT DD_RETENTION_LOCK_GOVERNANCE EMCLM 1 permanent uncounted \
                               VENDOR_STRING="LOCKING_ID=CRK00224110279;PRODUCT_LINE=Data \
                               Domain \
                               OS;FEATURE_NAME=RETENTION-LOCK-GOVERNANCE;UOM_CODE=IA;UOM_NAME=Instance \
                               per Server;PLC=DDO

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0177

OS;FEATURE_NAME=RETENTION-LOCK-GOVERNANCE;UOM_CODE=IA;UOM_NAME=Instance \
                               per Server;PLC=DDOS" HOSTID=ANY dist_info="ACTIVATED TO \
                               TELEFÓNICA CYBERSECURITY AND CLOUD TECH S.L." ISSUER=EMC \
                               ISSUED=10-Jul-2023 NOTICE="ACTIVATED TO License Site Number: \




Controller upgrade
                                                                64/69
  Dell Customer Communication - Confidential




                               1005820526" SN=1000541220 SIGN="0068 5AC2 CC7C 0B30 E67B 999A \
                               D016 4600 23AA 6E8D 00EB C00D E370 9CFE 661B"
                      INCREMENT DD_ENCRYPTION EMCLM 1.0 permanent uncounted \
                               VENDOR_STRING="LOCKING_ID=CRK00224110279;PRODUCT_LINE=Data \
                               Domain \
                               OS;FEATURE_NAME=ENCRYPTION;UOM_CODE=IA;UOM_NAME=Instance per \
                               Server;PLC=DDOS" HOSTID=ANY dist_info="ACTIVATED TO \
                               TELEFÓNICA CYBERSECURITY AND CLOUD TECH S.L." ISSUER=EMC \
                               ISSUED=10-Jul-2023 NOTICE="ACTIVATED TO License Site Number: \
                               1005820526" SN=1000541220 SIGN="0089 5AFE 7293 9811 1285 B729 \
                               D378 5700 20FC 29F0 2FAA 17F3 3D82 F367 57B0"
                      INCREMENT DD_DDBOOST EMCLM 1.0 permanent unc

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0179

S.L." ISSUER=EMC \
                               ISSUED=10-Jul-2023 NOTICE="ACTIVATED TO License Site Number: \
                               1005820526" SN=1000541220 SIGN="000B E413 D549 5594 56B2 970E \
                               E6FD 9C00 3285 0CA6 C261 89C3 837F 1E70 FCBA"
                      INCREMENT DD_VTL EMCLM 1.0 permanent uncounted \
                               VENDOR_STRING="LOCKING_ID=CRK00224110279;PRODUCT_LINE=Data \
                               Domain OS;FEATURE_NAME=VTL;UOM_CODE=IA;UOM_NAME=Instance per \
                               Server;PLC=DDOS" HOSTID=ANY dist_info="ACTIVATED TO \
                               TELEFÓNICA CYBERSECURITY AND CLOUD TECH S.L." ISSUER=EMC \
                               ISSUED=10-Jul-2023 NOTICE="ACTIVATED TO License Site Number: \
                               1005820526" SN=1000541220 SIGN="0076 BFBD FBEF 683A C782 4EAE \
                               9D27 8500 841C EFFD E216 431B B24B 26DC BBEF"
                      INCREMENT DD_RETENTION_LOCK_COMPLIANCE EMCLM 1.0 permanent uncounted \
                               VENDOR_STRING="LOCKING_ID=CRK00224110279;PRODUCT_LINE=Data \
                               Domain \
                               OS;FEATURE_NAME=RETENTION-LOCK-COMPLIANCE;UOM_CODE=IA;UOM_NAME=Instance \
                               per Server;PLC=DDOS" HOSTID=ANY dist_info="ACTIVATED TO \
                               TELEFÓNICA CYBERSECURITY AND CLOUD TECH S.L." ISSUER=EMC \

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0181

State   Expiration Date    Note
                      --   -------------------------   -----   ---------   -----   ---------------    -------------------
                      1    REPLICATION                     1   permanent   grace   n/a                Locking-id mismatch
                      2    VTL                             1   permanent   grace   n/a                Locking-id mismatch
                      3    DDBOOST                         1   permanent   grace   n/a                Locking-id mismatch
                      4    RETENTION-LOCK-GOVERNANCE       1   permanent   grace   n/a                Locking-id mismatch
                      5    ENCRYPTION                      1   permanent   grace   n/a                Locking-id mismatch
                      6    I/OS                            1   permanent   grace   n/a                Locking-id mismatch
                      7    RETENTION-LOCK-COMPLIANCE       1   permanent   grace   n/a                Locking-id mismatch
                      --   -------------------------   -----   ---------   -----   ---------------    -------------------

                      New licenses:

                      Capacity licenses:
                      ##   Feature           Shelf Model    Capacity     Type        State    Expiration Date   Note
                      --   ---------------   ------------   ----------   ---------   ------   ---------------   ----
                      1    CAPACITY-ACTIVE   HIGH_DEN

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0182

--   ---------------   ------------   ----------   ---------   ------   ---------------   ----
                      1    CAPACITY-ACTIVE   HIGH_DENSITY   785.80 TiB   permanent   active   n/a
                      --   ---------------   ------------   ----------   ---------   ------   ---------------    ----
                      Licensed Active Tier capacity: 785.80 TiB*
                      * Depending on the hardware platform, usable filesystem capacities may vary.

                      Feature licenses:
                      ##   Feature                     Count   Type        State    Expiration Date   Note




Controller upgrade
                                                                65/69
  Dell Customer Communication - Confidential




                      --   -------------------------   -----   ---------   ------   ---------------      ----
                      1    REPLICATION                     1   permanent   active   n/a
                      2    I/OS                            1   permanent   active   n/a
                      3    RETENTION-LOCK-GOVERNANCE       1   permanent   active   n/a
                      4    ENCRYPTION                      1   permanent   active   n/a
                      5    DDBOOST                         1   permanent   active   n/a
                      6    VTL                             1   permanent   active   n/a
                      7    RETENTION-LOCK-COMPLIANCE       1   permanent   active   n/a

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0183

1   permanent   active   n/a
                      7    RETENTION-LOCK-COMPLIANCE       1   permanent   active   n/a
                      --   -------------------------   -----   ---------   ------   ---------------      ----

                      ** New license(s) will overwrite all existing license(s).

                      Do you want to proceed? (yes|no) [yes]: yes


                      eLicense(s) updated.
                      sysadmin@vdc-dd5#
                      sysadmin@vdc-dd5# alerts show current
                      No active alerts.
                      sysadmin@vdc-dd5# elicense show
                      System locking-id: CRK00224110279

                      Licensing scheme: EMC Electronic License Management System (ELMS) node-locked mode

                      Capacity licenses:
                      ##   Feature           Shelf Model    Capacity     Type        State    Expiration Date   Note
                      --   ---------------   ------------   ----------   ---------   ------   ---------------   ----
                      1    CAPACITY-ACTIVE   HIGH_DENSITY   785.80 TiB   permanent   active   n/a
                      --   ---------------   ------------   ----------   ---------   ------   ---------------   ----
                      Licensed Active Tier capacity: 785.80 TiB*
                      * Depending on the hardware platform, usable filesystem capacities may vary.

                      Feature licenses:

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0184

.80 TiB*
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
                      7    RETENTION-LOCK-COMPLIANCE       1   permanent   active   n/a
                      --   -------------------------   -----   ---------   ------   ---------------      ----
                      License file last modified at : 2023/07/11 15:49:42.
                      sysadmin@vdc-dd5# date
                      Tue Jul 11 15:50:01 CEST 2023
                      sysadmin@vdc-dd5#




                     5.12 ACTUALIZAR REGISTRO EN EL ESRS GATEWAY
                     Actualizar el registro en el ESRS Gateway para reflejar el nuevo número de serie del sistema.

---
_Generated manually from indexed chunks. No background processing._
