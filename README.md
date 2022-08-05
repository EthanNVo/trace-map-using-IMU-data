# Final Project Trace Map

Part of the Final Project of Pablo, Hector, William, and Ethan

Takes accelerometer and gyroscope data from an iPhone and outputs an array of positions along with an image of those positions plotted. 


The algorithm uses [Fusion](https://github.com/xioTechnologies/Fusion) to obtain a measurement of acceleration in the Earth coordinate frame from gyroscope and accelerometer data. This part of the code repurposes code from this [Gait-Tracking project](https://github.com/xioTechnologies/Gait-Tracking) 

Acceleration is then integrated into velocity which is integrated again into position.

The repository includes code for [finding position from accelerometer and gyroscope data](https://github.com/RandomN0body/trace-map-using-IMU-data/blob/main/trace_position.py), and code for [plotting that data onto a plot](https://github.com/RandomN0body/trace-map-using-IMU-data/blob/main/plot_position.py).

Included below is an example of a trace map produced from data that is also included in the repository called [newTestData.json](https://github.com/RandomN0body/trace-map-using-IMU-data/blob/main/newTestData.json)

| ![newTestData.json](https://media.discordapp.net/attachments/997235042826866780/1003455657514651718/unknown.png) |
|:--:|
| [Tracing position of user while using app (newTestData.json) |

