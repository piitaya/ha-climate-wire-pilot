# Pilot Wire pour Home Assistant

![Logo Pilot Wire](custom_components/pilot_wire/brand/icon.png)

[English version](README.md)

Un thermostat Home Assistant pour les radiateurs fil pilote : Qubino ZMNHJD1, Legrand et NodOn (ZHA, Zigbee2MQTT).

## Introduction

Certains modules fil pilote ne sont pas reconnus comme des thermostats dans Home Assistant :

- Les modules Zigbee (Legrand, NodOn, Adeo, VAV) apparaissent comme une entité `select`, avec ZHA ou Zigbee2MQTT.
- Le Qubino ZMNHJD1 apparaît comme une entité `light`, dont la luminosité choisit le mode (voir [Qubino et l'entité lumière](#qubino-et-lentité-lumière)).

Cette intégration crée une entité `climate` à partir de l'entité `select` ou `light`, pour piloter facilement votre radiateur.

Le thermostat a 2 modes :

- `heat` (chauffe), découpé en 5 presets :
  - `comfort` : mode Confort
  - `comfort-1` : mode Confort -1
  - `comfort-2` : mode Confort -2
  - `eco` : mode Éco
  - `away` : mode Hors-gel
- `off` : mode Arrêt

## Appareils compatibles

| Appareil                                | Modèle            | ZHA | Zigbee2MQTT | Z-Wave JS |
| :-------------------------------------- | :---------------- | :-- | :---------- | :-------- |
| Legrand sortie de câble fil pilote      | 064882            | ✅  | ✅          |           |
| NodOn module chauffage fil pilote       | SIN-4-FP-21       | ✅  | ✅          |           |
| NodOn module chauffage fil pilote       | SIN-4-FP-20       |     | ✅          |           |
| NodOn actionneur chauffage électrique   | FPS-4-1-00        |     | ✅          |           |
| Adeo Equation module fil pilote         | SIN-4-FP-21_EQU   | ✅  | ✅          |           |
| VAV module chauffage fil pilote         | VAV-256215-MOD1   |     | ✅          |           |
| Qubino Flush Pilot Wire                 | ZMNHJD1           |     |             | ✅        |

La sortie de câble Legrand doit d'abord être passée en mode fil pilote : réglez son « Device mode » sur fil pilote dans ZHA, ou `device_mode` sur `pilot_on` dans Zigbee2MQTT.

Si votre module n'apparaît pas quand vous ajoutez un thermostat, ouvrez une issue avec les options de son entité `select`.

## Installation

### HACS

[![Ouvrir votre instance Home Assistant et afficher ce dépôt dans HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=piitaya&repository=ha-pilot-wire&category=integration)

Ou dans HACS, ajoutez `https://github.com/piitaya/ha-pilot-wire` comme dépôt personnalisé de type « Intégration ». Téléchargez ensuite Pilot Wire et redémarrez Home Assistant.

### Manuelle

Copiez le dossier `custom_components/pilot_wire` dans le dossier `custom_components` de votre configuration Home Assistant, puis redémarrez Home Assistant.

## Configuration

[![Ouvrir votre instance Home Assistant et configurer Pilot Wire.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=pilot_wire)

Ou cherchez « Thermostat fil pilote » dans la page des intégrations ou des entrées, puis choisissez l'entité `select` ou `light` de votre radiateur.

## Capteur de puissance et action HVAC

Vous pouvez ajouter un capteur de puissance pour savoir si le radiateur chauffe vraiment. Le thermostat affiche alors son état en temps réel (`hvac_action`) :

- **Chauffe** : la consommation dépasse le seuil configuré
- **Inactif** : la consommation est sous le seuil

Quand le radiateur est éteint, l'action est toujours « Arrêt », avec ou sans capteur de puissance.

### Réglage

1. Choisissez un capteur de puissance (prise connectée, compteur d'énergie, etc.)
2. Indiquez un seuil de puissance en watts (0 W par défaut)
   - Au-dessus de ce seuil, le radiateur est considéré en chauffe
   - Par exemple, mettez 50 W si votre radiateur consomme plus de 50 W quand il chauffe

## Qubino et l'entité lumière

Le Qubino ZMNHJD1 n'utilise pas de commande Z-Wave dédiée au fil pilote. Il réutilise celle des variateurs, et chaque tranche de 10 % du niveau de variation choisit un mode. Z-Wave JS ne peut pas faire la différence, donc Home Assistant affiche le module comme une lumière à variateur. L'éteindre ou changer sa luminosité depuis une carte lumière change en réalité le mode du radiateur.

Cette intégration masque cette lumière et convertit la luminosité pour vous :

| Mode       | Luminosité    |
| :--------- | :------------ |
| Arrêt      | 0 à 10 %      |
| Hors-gel   | 11 à 20 %     |
| Éco        | 21 à 30 %     |
| Confort -2 | 31 à 40 %     |
| Confort -1 | 41 à 50 %     |
| Confort    | 51 à 100 %    |

Quand vous ajoutez un thermostat, seules les lumières d'un appareil Qubino sont proposées.
