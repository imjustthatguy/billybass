from adafruit_motorkit import MotorKit
import coloredlogs
import logging
import threading
import time

"""
Author: Jeremy Hernandez
Date: 05/15/2019
Purpose: Extension for alexa pi that allows for the billy bass fish 
	 animatronic to be responsive to voice commands by moving its motors
	 in a specified way.

Notes:   Controls the synchronization of the fish speaking and alexa talking as
	 many users that have implemented a talking alexa animatronic bought
	 sound sensors and mic amplifiers that solder onto pcb breadboards that listen for audio coming from the speakers. They then check to see if alexa is speaking through that device and move the animatronic motors respectively.
	 This is inefficent in many ways as it can pick up sounds from outside sources and move its motors when alexa isn't speaking.
	 Furthermore, it is more difficult in a sense that you can't control (or atleast harder) the animatornic to do different things based on the functions the alexapi service is calling
	 because it's only moving the motors based on a single sound input. This method controls the motors based on the requests being sent to the service, which allows us to define what constitutes a query, response, playlist
	 It is also costly and requires more advanced knowledge in soldering and electronics.

	 Thank you to the AlexaPi community for creating the AlexaPi package that
	 allows for the alexa service to work on any device. Without it this
	 wouldn't be possible.
"""

#IDEA: Implement abstract base class that allows for any animatronic to be responsive to amazon's alexa services (through the alexa pi package)

#styles
coloredlogs.DEFAULT_FIELD_STYLES = {
	'hostname': {'color': 'magenta'},
	'programname': {'color': 'cyan'},
	'name': {'color': 'blue'},
	'levelname': {'color': 'magenta', 'bold': True},
	'asctime': {'color': 'green'}
}
coloredlogs.DEFAULT_LEVEL_STYLES = {
	'info': {'color': 'blue'},
	'critical': {'color': 'red', 'bold': True},
	'error': {'color': 'red'},
	'debug': {'color': 'green'},
	'warning': {'color': 'yellow'}
}

coloredlogs.DEFAULT_LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
logger = logging.getLogger(__name__)

class BillyBass(threading.Thread):
	"""
		Purpose:
			Executes commands that move the motors of the billy bass animatronic.
			These commands represent different things the animatronic can do, such as move it's head, tail, or mouth.
			Commands are run by passing it through the constructor via its task parameter, which subsequently executes that command if it is valid. 
			Once the function has executed, the object is destroyed because it inherits threading behaviors

		Behavior:
			Inherits multithreading. This allows the fish to respond to the voice commands by moving its motors
			while at the same time outputting the audio coming from alexapi. It also allows for it to listen for other voice commands while its executing. 
		Usage:
			It is highly recommended to utilize this class using the with keyword as it will handle resource management without having to explicitly close the threads. This is because this class is a context manager.
			ex) with billybass(task="greet"):
				--enter code here if necessary--
	"""
	def __init__(self, task):
		"""
			Constructor calls superclass(threading) to set up its appropriate variables
			It also initalizes the adafruit motorkit, which we need in order to manipulate the motors of the animatronic.
			:param task: string that represents a command to the alexa service is being executed ( ex) When querying alexa
		"""
		threading.Thread.__init__(self)
		self.kit = MotorKit()
		self.task = task
		self.done = False

		#this defines the two motors in a dictionary for ease of access
		#and to keep things DRY
		self.motor = {
					"body": self.kit.motor1,
					"mouth": self.kit.motor2
					}
		logger.info("Billybass thread initialized")

	def __enter__(self):
		"""
			Magic method that is called when the class is being instantiated 
			with the 'with' keyword (context manager protocol). This method allows us to define what function to execute based on the task given in the constructor variable.
			If the task is illegal or does not exist, we raise an exception.

			Using context managers gives us the security in knowing the thread
			that is spawned when this class is instantiated is being released without having to deal with releasing it explicitly in the code that calls it. (__exit__ frees the resource)

		"""
		#i hate the redundancy of if-elif control blocks when checking against the same variable   
		#TODO: minimize redundancy of this function
		#defines what function execute based on the task
		if self.task == "greet":
			self.exec = self.greet
		elif self.task == "move_head":
			self.exec = self.move_head
		elif self.task == "move_tail":
			self.exec = self.move_tail
		elif self.task == "move_mouth":
			self.exec = self.move_mouth
		elif self.task == "trigger":
			self.exec = self.trigger
		elif self.task  == "response":
			self.exec = self.response
		elif self.task == "dance":
			self.exec = self.dance
		elif self.task == "reset":
			self.exec = self.reset_motors
		else:
			raise ValueError("Task does not exist for billy bass")

		logger.debug("Task initialized (" + self.task + ")")
		#runs the thread
		self.start()



	def __exit__(self, exc_type, exc_val, exc_tb):
		"""
			Called once were exiting from the with statement.
		"""
		self.stop()

	def release_motor(self,sensitivity):
		"""
			Releases motor by sleeping for a specified amount of time
			:param sensitivity: time in seconds to sleep for
		"""
		logger.debug("Releasing motor for " + str(sensitivity) + " seconds")
		time.sleep(sensitivity)

	@staticmethod
	def set_debug(DEBUG):
		"""
			Sets the debug level. Used primarily for debugging purposes
			:param DEBUG: boolean indicating whether to set log_level to debug or not
		"""
		try:
			if DEBUG:
				log_level = logging.DEBUG

			else:
				log_level = logging.INFO

			coloredlogs.install(log_level)
			logger.info("Debug mode: " + str(DEBUG))

		except Exception as e:
			logger.info("Invalid call to the set_debug function")
			logger.debug(str(e))

	def trigger(self):
		"""
			Moves head and mouth of the billybass fish. This should be called
			when the user triggers alexa for a query so that the fish mimics responsiveness
		"""
		logger.debug("Responding to trigger word")
		self.move_head()
		self.move_mouth()

	def response(self):
		"""
			Moves mouth of billybass fish when alexa is responding
			to a query the user requested.
			NOTE: This function is redundant in a sense that it only calls one function and debug logs. However I implemented it this way
				because there may be multiple ways the billybass fish can respond to a query (it can move its head and tail as well)
				so its nice to know I don't have to mess around with the actual function that moves the motors and instead can mess around with it here.
		"""
		logger.debug("Responding to query")
		self.move_mouth()

	def greet(self):
		"""
			Moves mouth in a specific way when the alexapi service starts.
			When its first initalized, the alexapi service notifies it is ready to run by saying "hello"
		"""
		logger.debug("Greeting user")
		steps = []
		i = 1.0
		while i != -1.0:
			i-=.2
			steps.append(i)
		#print(steps)
		self.run_motor(motor=self.motor["mouth"], sensitivity=0.05, steps=steps)
		self.motor["mouth"].throttle = 0

	def dance(self):
		"""
			The fish can dance! Moves it's head and tail with a time buffer
			in between so we don't overload the fish with too much current!
			BUG: Fish stops dancing after a couple seconds of usage. I have a feeling it has something to do with
				thread synchronization as when the dance function is called in main.py
				it is continiously called which spawns more threads to execute the same function.

			The fish dances in main.py when we play a playlist
		"""

		logger.debug("Dancing to playlist")
		self.move_head()
		time.sleep(1)
		self.move_tail()

	def move_mouth(self):
		"""
			Moves the mouth of the billybass fish by controlling the motor that moves it's mouth
		"""
		logger.debug("Opening mouth")
		self.run_motor(motor=self.motor["mouth"], sensitivity=0.1, steps=[1, -1.0, 0.0])

	def move_head(self):
		"""
			Moves the head of the billybass fish by controlling the motor that moves it's body (negative values move head)
		"""
		logger.debug("Moving body")
		self.run_motor(motor=self.motor["body"], sensitivity=1.0, steps=[0.0, -1.0])

	def move_tail(self):
		"""
			Moves the tail of the billybass fish by controlling the motor that moves it's body (positive values move tail)
		"""
		logger.debug("Moving tail")
		self.run_motor(motor=self.motor["body"], sensitivity=1.0, steps=[0.0, 1.0, 0.0])

	def run(self):
		"""
			When the thread is executed it runs this method
			It keeps executing until were told to stop. (self.done)
			If any errors occur we output to the user and raise the exception
		"""
		logger.debug("Executing")
		try:
			while not self.done:
				self.exec()
				time.sleep(.2)
		except Exception as e:
			logger.error(str(e))
			raise #propogate the exception

	def stop(self):
		"""
			Stops execution of the thread by setting this flag to
			true. Once execution of the thread has finished, it will
			free its resources
		"""
		logger.debug("Thread finished")
		self.done = True

	def run_motor(self, motor, sensitivity, steps):
		"""
			:param motor: which motor to run this on (mouth or body)
			:param sensitivity: delays the time between steps. The higher the value, the longer it will wait (measured in seconds)
			:param steps: list of floats that represent a sequence of positions on where to move the motor to [value of motor can only -1 <= x <= 1.
		"""

		logger.debug("Running motor " + str(motor) + ". \nSensitivity: " + str(sensitivity) + "\nSteps:" + str(steps))
		for step in steps:
			motor.throttle = step
			self.release_motor(sensitivity)

	def reset_motors(self):
		"""
			Helper function that resets both of the positions of the 
			motors to their default values
		"""
		logger.debug("Resetting motor values to 0")
		for motor_name, motor_object in self.motor.items():
			motor_object.throttle = 0.0
def main():
	pass
	#BillyBass.set_debug(True)
	#with BillyBass(task="dance"):
	#	print("Hello")
	#while True:
	#	try:
	#		time.sleep(.3)
	#		with BillyBass(task="response"):
	#
	#		print("Yaa")
	#	except KeyboardInterrupt:
	#		break
	#print("broke loop")
	#time.sleep(5)
	#with BillyBass(task="reset"):
	#	print("yaaaa")	
if __name__ == "__main__":
	main()




