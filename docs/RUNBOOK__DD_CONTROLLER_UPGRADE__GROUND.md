# DD Controller Upgrade — Grounded Runbook (VFMS v0)

**Scope:** Controller upgrade / controller swap procedure grounded from VFMS extracted chunks.  
**Source doc:** TA-ControllerUpgrade_Telefonica_DD9900.pdf  
**Doc ID:** 20251224_130922_532031  
**Rule:** No invented steps. If unclear → stop and collect missing info.

---

## 5) CAMBIO DE CONTROLADORA — Table of Contents (from source)
- 5.1 APAGAR LA CONTROLADORA ORIGEN
- 5.2 CAMBIO FÍSICO DE CONTROLADORA
- 5.3 CONFIGURAR LA CONTROLADORA DE DESTINO
- 5.4 RECUPERAR Y VERIFICAR CONFIGURACIÓN SCSI TARGET
- 5.5 VERIFICACIÓN CONFIGURACIÓN CLOUD TIER
- 5.6 VERIFICAR RED Y CONECTIVIDAD
- 5.7 VERIFICAR CIFS/NFS/DDBOOST
- 5.8 VERIFICAR FILE SYSTEM
- 5.9 VERIFICAR REPLICACIÓN
- 5.10 ACTUALIZAR IPMI

---

## 5.1 APAGAR LA CONTROLADORA ORIGEN

# VFMS v0 Grounded Output

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

## 5.2 CAMBIO FÍSICO DE CONTROLADORA

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

## 5.3 CONFIGURAR LA CONTROLADORA DE DESTINO

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

---

## 5.5 VERIFICACIÓN CONFIGURACIÓN CLOUD TIER

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

---

## 5.6 VERIFICAR RED Y CONECTIVIDAD

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

## 5.7 VERIFICAR CIFS/NFS/DDBOOST

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

---

## 5.8 VERIFICAR FILE SYSTEM

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

## 5.9 VERIFICAR REPLICACIÓN

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

## 5.10 ACTUALIZAR IPMI

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
