# HOME ASSISTANT 基于MQTT自定义灯插件
该插件可通过HACS ---> Custom repositories 引入并下载。

使用该插件，需先配置Home Asssistant MQTT服务。

下载插件后，可通过配置configuration.yaml，配置相关MQTT指令主题，示例：

```sh
light:
  - platform: mqtt_light_custom
    name: "我的MQTT灯"
    command_topic: "my/light/set"
    state_topic: "my/light/state"
    brightness_command_topic: "my/light/brightness/set"
    brightness_state_topic: "my/light/brightness/state"
    rgb_command_topic: "my/light/rgb/set"
    rgb_state_topic: "my/light/rgb/state"
```

