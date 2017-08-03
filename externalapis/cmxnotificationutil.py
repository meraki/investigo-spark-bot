import json

"""
def subscribe_area_change_notification(macAddress, trackedArea):
    #https://msesandbox.cisco.com:8081/apidocs/configuration-api#Notification-subscription-API-GET-Get-all-notificaiton-subscriptions

    users  = db.session.query(User).all()
    locations = [] #get hotspots that will trigger interaction
    print (users)
    data = {}
    
    
    name = "{}_{}_{}".format("cenu", "areachange", "event-trigger")
    data["name"] = name

    notificationType = "EVENT_DRIVEN"
    data["notificationType"] = notificationType
    
    #"notificationType": "Movement"
  
    receiver = {}
    #data["NotificationReceiverInfo"] 
    
    subscribedEvents = {}
    data["subscribedEvents"] = subscribedEvents
    
    extra1 = {}
    extra1["key"] = "moveDistanceInFt"
    extra1["value"] = "1"
    extras = {}
    extras.append(extra1)
    
    subscribedEvents.append(create_subscription_event(type="MovementEventTrigger", eventEntity="WIRELESS_CLIENTS", macAddress=macAddress, extras=extras))
    
    payload = json.dumps(data)
    
    subscribe_notifications(payload)
    
    {
      "name": "learning_movement2345",
      "userId": "learning",
      "rules": [
        {
          "conditions": [
            {
              "condition": "movement.distance > 50"
            },
            {
              "condition": "movement.hierarchy == DevNetCampus>DevNetBuilding>DevNetZone"
            },
            {
              "condition": "movement.macAddressList == 00:00:2a:01:00:1f;sahdkjsahdkjh askjdhla ksjd"
            },
            {
              "condition": "movement.deviceType == client"
            }
          ]
        }
      ],
      "subscribers": [
        {
          "receivers": [
            {
              "uri": "http://requestb.in:80/y0l3gty0",
              "messageFormat": "JSON",
              "qos": "AT_MOST_ONCE"
            }
          ]
        }
      ],
      "enabled": true,
      "enableMacScrambling": true,
      "notificationType": "Movement"
    }
    """

def create_subscription_event(type, eventEntity, extras, macAddress=None):
    output = {}
    output["type"] = type
    output["eventEntity"] = eventEntity
    
    if (macAddress is not None):
        output["macAddress"] = macAddress
    
    for extra in extras:
        output[str(extra["key"])] = extra["value"]
    
    return output


def subscribe_notification_subscriber():
    #https://developer.cisco.com/site/cmx-mobility-services/documents/api-reference-manual/#notification-api
    output = {}
    
    key = "NotificationReceiverInfo"
    
    trans = {}
    receiverInfo = {}
    
    receiverInfo["transport"] = trans
    trans["type"] = "TransportHttp"
    #trans["hostAddress"] = app.config.from_object(os.environ['PUBLIC_IP'])
    trans["hostAddress"] = "cenu-dev.herokuapp.com" 
    trans["port"] = 80
    trans["https"] = False
    PATH_NOTIFICATIONS_WEBHOOK = "/cmx_webhook"
    trans["urlPath"] = PATH_NOTIFICATIONS_WEBHOOK
    
    output = receiverInfo
    return output


def mount_subscription_json(name, notification_type, enable_MAC_scrambling=False):
    subscribers = subscribe_notification_subscriber()
    
    data = {}
    data["NotificationReceiverInfo"] = subscribers
    data["dataFormat"] = "JSON"
    data["enabled"] = True
    data["name"] = name
    data["enableMacScrambling"] = enable_MAC_scrambling
    data["notificationType"] = notification_type
    
    
    output = json.dumps(data)
    
    return output

def mount_subscriber_json(uri, qos="AT_MOST_ONCE", messageFormat="JSON"):
    """
        "subscribers": [
        {
          "receivers": [
            {
              "uri": "http://requestb.in:80/y0l3gty0",
              "messageFormat": "JSON",
              "qos": "AT_MOST_ONCE"
            }
          ]
        }
      ]
    """
    
    output = {}
    receivers = {}
    receiver = {}
    
    receiver["uri"] = uri
    receiver["messageFormat"] = messageFormat
    receiver["qos"] = qos
    
    receivers = [receiver]
    output["receivers"] = receivers
    return [output]


def mount_notification_json(userId, name, notificationType, conditions, notification_uri, enable_MAC_scrambling=False):
    data = {} 
    data["enabled"] = True
    data["name"] = name
    data["userId"] = userId
    data["enableMacScrambling"] = enable_MAC_scrambling
    data["notificationType"] = notificationType

    subscribers = mount_subscriber_json(notification_uri)
    data["subscribers"] = subscribers
    data["rules"] = [mount_notification_rules(conditions)]
    
    output = json.dumps(data)
    return output

def mount_notification_rules(conditions):
    
    data = {}
    set = []
    
    for c in conditions:
        rule = {}
        rule["condition"] = c
        set.append(rule)
    
    data["conditions"] = set
    return data

if __name__ == '__main__':
    conditions = ["movement.distance > 50", "movement.hierarchy == DevNetCampus>DevNetBuilding>DevNetZone", "movement.macAddressList == 00:00:2a:01:00:1f;", "movement.deviceType == client"]
    payload = mount_notification_json("learning", "learning_movement", conditions)
    print (json.dumps(payload, indent=4, sort_keys=True)) 