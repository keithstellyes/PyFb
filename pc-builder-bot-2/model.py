from pcpartpicker import API
import pickle, random

PARTS = None
api = API()
INTEL = 'Intel'
AMD = 'AMD'
CPU_BRANDS = set((AMD, INTEL))
HZ_IN_GHZ = 1_000_000_000
HZ_IN_MHZ = 1_000_000
BYTES_IN_GB = 1_000_000_000

try:
	PARTS = pickle.load(open('parts.pkl', 'rb'))
	print('parts successfully loaded from local pickle')
except FileNotFoundError:
	print('Couldn\'t find parts pickle, downloading...')
	PARTS = api.retrieve_all()
	pickle.dump(PARTS, open('parts.pkl', 'wb'))

class Computer:
	def __init__(self):
		self.cpu = None
		self.mobo = None
		self.case = None
		self.psu = None
		self.memory = {}
		self.storage = {}

	def __str__(self):
		return str(self.__dict__)

	def __repr__(self):
		return str(self)

def all_sockets():
	return set([mobo.socket for mobo in PARTS['motherboard']])

def intel_sockets():
	chips = ('Atom', 'Pentium', 'Celeron', 'Xeon')
	sockets = set()
	for socket in all_sockets():
		if 'LGA' in socket:
			sockets.add(socket)
		else:
			for chip in chips:
				if chip in socket:
					sockets.add(socket)
					break
	return sockets

def amd_sockets():
	return all_sockets() - intel_sockets()

def compatible_cpu_and_mobo(cpu, mobo):
	if cpu is None or mobo is None:
		return True
	if cpu.brand == INTEL:
		return mobo.socket in intel_sockets()
	return mobo.socket in amd_sockets()

def compatible_case_and_mobo(case, mobo):
	return True

def possible_cpu(pc, cpu):
	return compatible_cpu_and_mobo(cpu, pc.motherboard)

def all_possible_cpu(pc):
	return [cpu for cpu in PARTS['cpu'] if possible_cpu(pc, cpu)]

def possible_mobo(pc, mobo):
	return compatible_cpu_and_mobo(pc.cpu, mobo)

def all_possible_mobo(pc):
	return [mobo for mobo in PARTS['motherboard'] if possible_mobo(pc, mobo)]

def pstr_cpu(cpu):
	return '{brand} {model} {corenum} cores @{ghz}GHz'.format(brand=cpu.brand, 
		model=cpu.model, corenum=cpu.cores, ghz=cpu.base_clock.cycles / HZ_IN_GHZ)

def pstr_mobo(mobo):
	return '{brand} {model} ({socket} socket)'.format(brand=mobo.brand, model=mobo.model, socket=mobo.socket)

def pstr_case(case):
	return '{} {}'.format(case.brand, case.model)

def pstr_psu(psu):
	return '{} {} {}W'.format(psu.brand, psu.model, psu.wattage)

def pstr_memory(mem):
	return '{} {} {} {}MHz'.format(mem.brand, mem.model, mem.module_type, mem.speed.cycles // HZ_IN_MHZ)

def pstr_storage(storage):
	gb = storage.capacity.total // BYTES_IN_GB
	capacity = '{}GB'.format(gb) if gb < 1000 else '{}TB'.format(gb // 1000)
	return '{} {} {} {}'.format(storage.brand, storage.model, capacity, storage.storage_type)

def pstr_pc(pc):
	s = 'CPU: {}\n'.format(pstr_cpu(pc.cpu))
	s += 'Motherboard: {}\n'.format(pstr_mobo(pc.mobo))
	s += 'Case: {}\n'.format(pstr_case(pc.case))
	s += 'PSU: {}\n'.format(pstr_psu(pc.psu))
	s += 'RAM: {}\n'.format(','.join(['{}x {}'.format(pc.memory[m], pstr_memory(m)) for m in pc.memory.keys()]))
	s += 'Storage: {}'.format(','.join(['{}x {}'.format(pc.storage[s], pstr_storage(s)) for s in pc.storage.keys()]))
	return s

def random_pc():
	pc = Computer()
	pc.cpu = random.choice(PARTS['cpu'])
	pc.mobo = random.choice(all_possible_mobo(pc))
	pc.case = random.choice(PARTS['case'])
	pc.psu = random.choice(PARTS['power-supply'])
	pc.memory[random.choice(PARTS['memory'])] = random.choice((1, 2, 4))
	pc.storage[random.choice(PARTS['internal-hard-drive'])] = random.randint(1, 3)
	return pc