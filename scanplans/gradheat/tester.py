from ophyd.sim import hw
from gradient_heating import gradient_heating_plan
from utils import calib_map_gen

ns = hw()
# plan for calibration run
p = gradient_heating_plan([pe1c, cs700], 5, {},
                          ns.motor1, 3.6, ns.motor2, 2.5,
                          1 # one round
                          )
# plan for sample run
#calib_map = calib_map_gen(poni_dir)
#p = gradient_heating_plan([pe1c, cs700], 5,
#                          calib_map,
#                          ns.motor1, 3.6, ns.motor2, 2.5,
#                          3 # three rounds
#                          )
