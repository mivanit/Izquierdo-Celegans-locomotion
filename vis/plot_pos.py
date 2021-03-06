from typing import *

import numpy as np
import numpy.lib.recfunctions as rfn

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation

WORM_RADIUS = 80e-6

def arr_bounds(
		arr, 
		pad_frac : float = 0.0,
	):
	arr_min = np.amin(arr)
	arr_max = np.amax(arr)
	
	arr_range = arr_max - arr_min

	arr_min = arr_min - arr_range * pad_frac
	arr_max = arr_max + arr_range * pad_frac

	return (arr_min, arr_max)

def read_body_data(filename):
		data_raw = np.genfromtxt(filename, delimiter = ' ', dtype = None)

		data_raw = data_raw[:,1:]

		n_tstep = data_raw.shape[0]
		n_seg = int(data_raw.shape[1] / 3)

		data = np.full(
			shape = (n_tstep, n_seg),
			fill_value = np.nan,
			dtype = np.dtype([ ('x','f8'), ('y','f8'), ('phi','f8') ]),
		)

		for s in range(n_seg):
			data[:, s]['x'] = data_raw[:, s*3]
			data[:, s]['y'] = data_raw[:, s*3 + 1]
			data[:, s]['phi'] = data_raw[:, s*3 + 2]

		return data

def _plot_collision_boxes(ax, blocks, vecs):
	from matplotlib.patches import Rectangle
	from matplotlib.collections import PatchCollection

	print(blocks)
	print(vecs)

	plot_boxes = []

	for bl in blocks:
		plot_boxes.append(Rectangle(
			xy = bl[0], 
			width = bl[1][0] - bl[0][0], 
			height = bl[1][1] - bl[0][1],
			fill = True,
		))

	pc = PatchCollection(
		plot_boxes, 
		facecolor = 'red', 
		alpha = 0.5,
		edgecolor = 'red',
	)

	ax.add_collection(pc)

def read_coll_objs_file(objs_file : str):
	blocks = []
	vecs = []
	
	with open(objs_file, 'r') as fin:
		for row in fin:
			row_lst = row.strip().split()
			row_lst = [ float(x) for x in row_lst ]

			blocks.append([ row_lst[0:2], row_lst[2:4] ])
			vecs.append(row_lst[4:])

	return (np.array(blocks), np.array(vecs))


def body_data_split_DV(data):
	n_tstep = data.shape[0]
	n_seg = data.shape[1]

	worm_thickness = (
		WORM_RADIUS / 2.0 * abs(
			np.sin(np.arccos(
				((np.linspace(0,n_seg,n_seg)) - n_seg / 2.0) 
				/ ( n_seg / 2.0 + 0.2)
			))
		)
	)

	data_Dorsal = np.full(
		shape = (n_tstep, n_seg),
		fill_value = np.nan,
		dtype = np.dtype([ ('x','f8'), ('y','f8')]),
	)

	data_Ventral = np.full(
		shape = (n_tstep, n_seg),
		fill_value = np.nan,
		dtype = np.dtype([ ('x','f8'), ('y','f8')]),
	)

	for t in range(n_tstep):
		dX = worm_thickness * np.cos(data[t]['phi'])
		dY = worm_thickness * np.sin(data[t]['phi'])
		data_Dorsal[t]['x'] = data[t]['x'] + dX
		data_Dorsal[t]['y'] = data[t]['y'] + dY   
		data_Ventral[t]['x'] = data[t]['x'] - dX   
		data_Ventral[t]['y'] = data[t]['y'] - dY 

	return (data_Dorsal, data_Ventral)




class Plotters(object):
	@staticmethod
	def head_pos(filename : str = 'data/run/body.dat', collision_objs_file : str = 'data/collision_objs.tsv'):
		head_x = []
		head_y = []
		
		with open(filename, 'r') as fin:
			for line in fin:
				xy_temp = line.split()[1:3]
				head_x.append(float(xy_temp[0]))
				head_y.append(float(xy_temp[1]))

		blocks,vecs = read_coll_objs_file(collision_objs_file)
		
		
		fig, ax = plt.subplots(1,1)
		_plot_collision_boxes(ax, blocks, vecs)

		print(len(head_x), len(head_y))
		plt.axis('equal')
		plt.plot(head_x, head_y)
		plt.show()

	@staticmethod
	def anim(
			filename : str = 'data/run/body.dat',
			collision_objs_file : str = 'data/collision_objs.tsv',
			out_file : str = 'data/worm.mp4',
			arrbd_x = None,
			arrbd_y = None,
			limit_frames : Optional[int] = None,
			figsize_scalar : float = 10.0,
		):
		"""
		https://towardsdatascience.com/animations-with-matplotlib-d96375c5442c
		credit to the above for info on how to use FuncAnimation
		"""
		# idk what this does tbh
		matplotlib.use("Agg")
		
		# read the data
		data = read_body_data(filename)
		if limit_frames is not None:
			data = data[:limit_frames]

		# process it
		data_D, data_V = body_data_split_DV(data)
		

		blocks,vecs = read_coll_objs_file(collision_objs_file)

		# set up the figure object
		if arrbd_x is None:
			# arrbd_x = arr_bounds(data['x'])
			arrbd_x = (np.amin(blocks[:,:,0]), np.amax(blocks[:,:,0]))
		else:
			arrbd_x = tuple(arrbd_x)

		if arrbd_y is None:
			# arrbd_y = arr_bounds(data['y'])
			arrbd_y = (np.amin(blocks[:,:,1]), np.amax(blocks[:,:,1]))
		else:
			arrbd_y = tuple(arrbd_y)
		
		print('> positional bounds:\t', arrbd_x, arrbd_y)
	
		figsize = np.array([
			arrbd_x[1] - arrbd_x[0],
			arrbd_y[1] - arrbd_y[0],
		])
		
		# print(f'> figsize:\t{figsize}')
		figsize = figsize * figsize_scalar / max(figsize)
		print(f'> figsize:\t{figsize}')
		fig, ax = plt.subplots(1, 1, figsize = figsize)
		# fig, ax = plt.subplots(1, 1)
		
		# ax.set_xlim(*arrbd_x)
		# ax.set_ylim(*arrbd_y)

		# plt.xlim(*arrbd_x)
		# plt.ylim(*arrbd_y)

		# fix the scaling
		ax.axis('equal')
		# plt.axis('equal')

		# draw the blocks
		_plot_collision_boxes(ax, blocks, vecs)
		
		# Set up formatting for the movie files
		Writer = animation.writers['ffmpeg']
		writer = Writer(fps=30, metadata=dict(artist='Me'), bitrate=1800)

		# this function gets called on each frame
		def anim_update(i, line_D, line_V):
			print(f'\t{i}\t/\t{data.shape[0]}', end = '\r')
			plt.title(f'frame   {i}')
			line_D.set_data(data_D[i]['x'], data_D[i]['y'])
			line_V.set_data(data_V[i]['x'], data_V[i]['y'])

			return line_D,line_V
		
		# set up the base worm
		line_D, = ax.plot([], [], 'r-')
		line_V, = ax.plot([], [], 'b-')

		print('> finished setup!')

		# make the animation
		line_ani = animation.FuncAnimation(
			fig, 
			anim_update,
			fargs = (line_D, line_V),
			frames = data.shape[0],
			interval = 50, 
			blit=True,
		)

		print(f'> animation created, saving to file `{out_file}`')

		# save it
		line_ani.save(out_file, writer = writer)

		print('\n\n> done saving!')



	@staticmethod
	def act(filename = 'data/run/act.dat'):
		data_raw = np.genfromtxt(filename, delimiter = ' ', dtype = np.float).T

		print(data_raw.shape, data_raw.dtype)

		T = data_raw[0]
		V = data_raw[1:]

		print(V.shape, V.dtype)

		plt.ylim(-50.0, 50.0)

		for vv in V:
			plt.plot(T, vv)

		plt.show()





if __name__ == '__main__':
	import fire

	fire.Fire(Plotters)


