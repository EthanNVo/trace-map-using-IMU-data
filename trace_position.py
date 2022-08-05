from dataclasses import dataclass
import matplotlib.pyplot as plt
import scipy as sp
from scipy.interpolate import interp1d
from scipy import integrate
import imufusion
import numpy as np
import math
from scipy import signal
import json

def trace_position(data_sample):
  # Import sensor data
  def load_tester(file):
      with open(file) as f:
          data = json.load(f)
      return np.asarray(data)
    
  data = load_tester(data_sample)

  sample_rate = 400  # 400 Hz

  orientation = data[:, 7:10]*180/np.pi

  timestamp = data[:, 0]/1000

  accelerometer = data[:, 1:4]

  gyroscope = data[:,4:7] * 180/np.pi
  gyroscope1 = np.empty((gyroscope.shape[0],gyroscope.shape[1]))

  def lpf(x, omega_c, T):
    #Implement a first-order low-pass filter.
    #The input data is x, the filter's cutoff frequency is omega_c [rad/s] and the sample time is T [s].  
    #The output is y.
    y = x
    alpha = (2-T*omega_c)/(2+T*omega_c)
    beta = T*omega_c/(2+T*omega_c)
    for k in range(1, np.size(t)):
        y[k] = alpha*y[k-1] + beta*(x[k]+x[k-1])
    return y

  
  #averaging gyrscope data to filter noise
  gyroscope1[:,0] = sp.integrate.trapz(gyroscope[:,0], x=timestamp)
  gyroscope1[:,1] = sp.integrate.trapz(gyroscope[:,1], x=timestamp)
  gyroscope1[:,2] = sp.integrate.trapz(gyroscope[:,2], x=timestamp)

  i = 0
  while i < gyroscope.shape[0]:
    orientation[i,0] = (orientation[i,0] + gyroscope1[i,0])/2
    orientation[i,1] = (orientation[i,1] + gyroscope1[i,1])/2
    orientation[i,2] = (orientation[i,2] + gyroscope1[i,2])/2
    i += 1

  gyroscope[:,0] = np.diff(orientation[:,0],prepend=gyroscope[0,0])
  gyroscope[:,1] = np.diff(orientation[:,1],prepend=gyroscope[0,1])
  gyroscope[:,2] = np.diff(orientation[:,2],prepend=gyroscope[0,2])
  
  # Intantiate AHRS algorithms
  offset = imufusion.Offset(sample_rate)
  ahrs = imufusion.Ahrs()

  ahrs.settings = imufusion.Settings(0.5,  # gain
                                    10,  # acceleration rejection
                                    0,  # magnetic rejection
                                    5 * sample_rate)  # rejection timeout = 5 seconds

  # Process sensor data
  delta_time = np.diff(timestamp, prepend=timestamp[0])

  euler = np.empty((len(timestamp), 3))
  internal_states = np.empty((len(timestamp), 3))
  acceleration = np.empty((len(timestamp), 3))

  for index in range(len(timestamp)):
      gyroscope[index] = offset.update(gyroscope[index])

      ahrs.update_no_magnetometer(gyroscope[index], accelerometer[index], delta_time[index])

      euler[index] = ahrs.quaternion.to_euler()

      ahrs_internal_states = ahrs.internal_states
      internal_states[index] = np.array([ahrs_internal_states.acceleration_error,
                                            ahrs_internal_states.accelerometer_ignored,
                                            ahrs_internal_states.acceleration_rejection_timer])

      acceleration[index] = 9.81 * ahrs.earth_acceleration  # convert g to m/s/s
  
  #convolution smoothing filter
  def smooth(y, box_pts):
      box = np.ones(box_pts)/box_pts
      y_smooth = np.convolve(y, box, mode='same')
      return y_smooth

  #smoothing acceleration data
  acceleration[:,0] = smooth(acceleration[:,0],15)
  acceleration[:,1] = smooth(acceleration[:,1],15)
  acceleration[:,2] = smooth(acceleration[:,2],15)

  # Identify moving periods
  is_moving = np.empty(len(timestamp))

  for index in range(len(timestamp)):
      is_moving[index] = np.sqrt(acceleration[index].dot(acceleration[index])) > 1.5  # threshold = 1.5 m/s/s

  margin = int(0.02 * sample_rate)  # 20 ms

  for index in range(len(timestamp) - margin):
      is_moving[index] = any(is_moving[index:(index + margin)])  # add leading margin

  for index in range(len(timestamp) - 1, margin, -1):
      is_moving[index] = any(is_moving[(index - margin):index])  # add trailing margin

  # Calculate velocity (includes integral drift)
  velocity = np.zeros((len(timestamp), 3))
  
  velocity[:,0] = sp.integrate.cumtrapz(acceleration[:,0],x=timestamp,initial=0)
  velocity[:,1] = sp.integrate.cumtrapz(acceleration[:,1],x=timestamp,initial=0)
  velocity[:,2] = sp.integrate.cumtrapz(acceleration[:,2],x=timestamp,initial=0)


  # Find start and stop indices of each moving period
  is_moving_diff = np.diff(is_moving, append=is_moving[-1])

  @dataclass
  class IsMovingPeriod:
      start_index: int = -1
      stop_index: int = -1


  is_moving_periods = []
  is_moving_period = IsMovingPeriod()

  for index in range(len(timestamp)):
      if is_moving_period.start_index == -1:
          if is_moving_diff[index] == 1:
              is_moving_period.start_index = index

      elif is_moving_period.stop_index == -1:
          if is_moving_diff[index] == -1:
              is_moving_period.stop_index = index
              is_moving_periods.append(is_moving_period)
              is_moving_period = IsMovingPeriod()

  # Remove integral drift from velocity
  velocity_drift = np.zeros((len(timestamp), 3))

  for is_moving_period in is_moving_periods:
      start_index = is_moving_period.start_index
      stop_index = is_moving_period.stop_index

      t = [timestamp[start_index], timestamp[stop_index]]
      x = [velocity[start_index, 0], velocity[stop_index, 0]]
      y = [velocity[start_index, 1], velocity[stop_index, 1]]
      z = [velocity[start_index, 2], velocity[stop_index, 2]]

      t_new = timestamp[start_index:(stop_index + 1)]

      velocity_drift[start_index:(stop_index + 1), 0] = interp1d(t, x)(t_new)
      velocity_drift[start_index:(stop_index + 1), 1] = interp1d(t, y)(t_new)
      velocity_drift[start_index:(stop_index + 1), 2] = interp1d(t, z)(t_new)

  velocity = velocity - velocity_drift

  # Calculate position
  position = np.zeros((len(timestamp), 3))

  #integrating position for velocity
  position[:,0] = sp.integrate.cumtrapz(velocity[:,0],x=timestamp,initial=0)
  position[:,1] = sp.integrate.cumtrapz(velocity[:,1],x=timestamp,initial=0)
  position[:,2] = sp.integrate.cumtrapz(velocity[:,2],x=timestamp,initial=0)

  end_start = False
  if end_start == True:
    position[-1, :] = position[0,:]
  
  return position
