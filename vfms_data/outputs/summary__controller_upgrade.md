# VFMS v0 Grounded Output

**Query:** controller upgrade

**Doc filter:** 20251224_130922_532031

## Sources (extracted chunks)

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0001

Dell Customer Communication - Confidential




                      “Controller upgrade” DD9900 TA




                 Preparado para:

                 TELEFÓNICA
                                             Preparado por:
                                             DELL EMC
                                             Ribera del Loira, 8-10
                                             28042 Madrid
                                             España
  Dell Customer Communication - Confidential




             Copyright © 2020 DELL EMC Corporation. All Rights Reserved.

             EMC believes the information in this publication is accurate of its publication date. The information is subject to change without
             notice.
             The information in this publication is provided “as is”. EMC Corporation makes no representations or warranties of any kind with
             respect to the information in this publication, and specifically disclaims implied warranties of merchantability or fitness for a
             particular purpose.
             Use, copying, and distribution of any EMC software described in this publication requires an applicable software license.
             For the most up-to-date listing of EMC product names, see EMC Corporation Trademarks on EMC.com.
             All other trademarks used herein are the property of their respective owners.




Controller upgrade
                                                                         2/6

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0002

erein are the property of their respective owners.




Controller upgrade
                                                                         2/69
  Dell Customer Communication - Confidential




                                                 Información del documento

                         Fecha salida            Julio 2023
                         Versión #               1.0
                         Autor


                                                     Histórico de versiones
                     Versión            Fecha                  Razón del cambio
                     1.0                Julio 2023             Versión inicial




                                                     Lista de distribución

                 Nombre                     Puesto                           Mail




Controller upgrade
                                                              3/69
  Dell Customer Communication - Confidential




             1 ÍNDICE DE CONTENIDOS
             1      ÍNDICE DE CONTENIDOS ........................................................................................................... 4
             2      INTRODUCCIÓN ........................................................................................................................ 5
             2.1        PLAN DE ACCIÓN............................................................................................................................... 5
             2.2        ARQU

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

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0007

A continuación, se indica el plan de acción a ejecutar.

                     2.1 PLAN DE ACCIÓN
             Se resumen los pasos a seguir:

                 0. Requisitos previos:
                       a. Requisitos ambientales adicionales
                              Model #   Power (VA) 110-120 / 200-240 V   Cooling BTU/hr   System Size   Shelf Size   Weight LBS
                               9400                 1981                     6441             2U         3U-5U           70
                               9900                 1236                     4228             3U           3U           110
                               FS25                 301 W                    1027             3U            -           44,6
                               DS60                  980                     3177             5U            -           225


                          b. Cableado eléctrico para la controladora destino (DD9900)




                          c. Cableado eléctrico para las bandejas adicionales




Controller upgrade
                                                                  5/69
  Dell Customer Communication - Confidential




                 1. PREVIO A HEADSWAP
                       a. Reorganizar layout actual del rack y enracar la controladora DD9900 con su bandeja FS25
                       b. Preparar la controladora destino (DD9900).
                          i.  Colocación de tarjetas I/O igual a controladora origen.

### TA-ControllerUpgrade_Telefonica_DD9900.pdf — 20251224_130922_532031_c0008

b. Preparar la controladora destino (DD9900).
                          i.  Colocación de tarjetas I/O igual a controladora origen.
                         ii.  Revisar que están cargadas las baterias de NVRAM .
                        iii.  Actualización a 7.7.4.0-1017976 de DD-OS, misma versión que la controladora origen
                              (DD9400).
                       c. Preparar la controladora origen (DD9400).
                          i.  Actualizar DD-OS a 7.7.4.0-1017976, misma versión que la controladora destino
                              (DD9900).

                 2. HEADSWAP
                      a. Quitar caché tier.
                      b. Retirada de DD9400 y reubicación en rack de DD9900 y de bandeja DS60 superior.
                      c. Recableado de interfaces ethernet, iDrac y SAS.




Controller upgrade
                                                           6/69
  Dell Customer Communication - Confidential




                      d. Headswap.
                      e. Agregar bandeja de caché tier.
                 3. AMPLIACIÓN
                      a. Conectar la bandeja DS60 nueva al Data Domain destino (DD9900).

                     2.2 ARQUITECTURA DEFINITIVA
             La solución Data Domain 9900 propuesta por EMC Computer Systems se compone de:

             1. Un sistema de deduplicación inline EMC DataDomain DD9900 con replicación optimizada.

             2. La configuración hardware asociada se dis

---
_Generated manually from indexed chunks. No background processing._
