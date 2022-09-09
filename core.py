import cv2
import numpy as np 
# import matplotlib.pyplot as plt 
import random
from k_means import kmeans
from gcgraph import GCGraph
import time

def timeit(func):
	def wrapper(*args, **kw):
		time1 = time.time()
		result = func(*args, **kw)
		time2 = time.time()
		# print(func.__name__, time2-time1)
		return result
	return wrapper

def get_size(img):
	return list(img.shape)[:2]

def flat(img):
	return img.reshape([1, img.size])[0]

class GMM:
	'''The GMM: Gaussian Mixture Model algorithm'''
	'''Each point in the image belongs to a GMM, and because each pixel owns
		three channels: RGB, so each component owns three means, 9 covs and a weight.'''
	
	def __init__(self, k = 5):
		'''k is the number of components of GMM'''
		self.k = k
		self.weights = np.asarray([0. for i in range(k)]) # Weight of each component
		self.means = np.asarray([[0., 0., 0.] for i in range(k)]) # Means of each component
		self.covs = np.asarray([[[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]] for i in range(k)]) # Covs of each component
		self.cov_inv = np.asarray([[[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]] for i in range(k)])
		self.cov_det = np.asarray([0. for i in range(k)])
		self.pixel_counts = np.asarray([0. for i in range(k)]) # Count of pixels in each components
		self.pixel_total_count = 0 # The total number of pixels in the GMM
		
		# The following two parameters are assistant parameters for counting pixels and calc. pars.
		self._sums = np.asarray([[0., 0., 0.] for i in range(k)])
		self._prods = np.asarray([[[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]] for i in range(k)])

	# @timeit
	def _prob_pixel_component(self, pixel, ci):
		'''Calculate the probability of each pixel belonging to the ci_th component of GMM'''
		'''Using the formula of multivariate normal distribution'''
		# print(self.cov_inv)
		inv = self.cov_inv[ci]
		det = self.cov_det[ci]
		t = pixel - self.means[ci]
		nt = np.asarray([t])
		mult = np.dot(inv, np.transpose(nt))
		mult = np.dot(nt, mult)
		# print(det)
		return (1/np.sqrt(det) * np.exp(-0.5*mult))[0][0]

	# @timeit
	def prob_pixel_GMM(self, pixel):	
		'''Calculate the probability of each pixel belonging to this GMM, which is the sum of 
			the prob. of the pixel belonging to each component * the weight of the component'''
		'''Also the first term of Gibbs Energy(negative;)'''
		return sum([self._prob_pixel_component(pixel, ci) * self.weights[ci] for ci in range(self.k)])

	# @timeit
	def most_likely_pixel_component(self, pixel):
		'''Calculate the most likely component that the pixel belongs to'''
		# g = np.vectorize(self._prob_pixel_component)
		# prob = np.asarray([g(pixel, ci) * self.weights[ci] for ci in range(self.k)])
		prob = np.asarray([self._prob_pixel_component(pixel, ci) for ci in range(self.k)])
		# print(prob.argmax(0))
		# print(prob.argmax(0))
		return prob.argmax(0)

	# @timeit
	# def vec_pix_comp(self, pixel):
	# 	f = np.vectorize(self.most_likely_pixel_component)
	# 	print(f(pixel))
	# 	return f(pixel)

	# @timeit
	def add_pixel(self, pixel, ci):
		'''Add a pixel to the ci_th component of GMM, and refresh the parameters'''
		# print(np.asarray(pixel))
		tp = pixel.copy().astype(np.float32)
		self._sums[ci] += tp
		tp.shape = (tp.size, 1)
		self._prods[ci] += np.dot(tp, np.transpose(tp))
		self.pixel_counts[ci] += 1
		self.pixel_total_count += 1

	def __learning(self):
		variance = 0.01
		zeros = np.where(np.asarray(self.pixel_counts) == 0)
		notzeros = np.where(np.asarray(self.pixel_counts) != 0)
		'''Learn the parameters with the data given; Also the 2th step in 'Iterative Minimization'.'''
		self.weights = np.asarray([self.pixel_counts[i]/self.pixel_total_count for i in range(self.k)]) # The weight of each comp. is the pixels in the comp. / total pixels.
		self.means = np.asarray([self._sums[i]/self.pixel_counts[i] for i in range(self.k)]) # The mean of each comp. is the sum of pixels of the comp. / the number of pixels in the comp.
		nm = np.asarray([[i] for i in self.means])
		self.covs = np.asarray([self._prods[i]/self.pixel_counts[i] - np.dot(np.transpose(nm[i]), nm[i]) for i in range(self.k)]) # The cov of each comp.
		self.cov_det = np.asarray([np.linalg.det(cov) for cov in self.covs])
		'''Avoid Singular Matrix'''
		for i in range(self.k):
			while self.cov_det[i] <= 0:
				self.covs[i] += np.diag([variance for i in range(3)])
				self.cov_det[i] = np.linalg.det(self.covs[i])
		self.cov_inv = np.asarray([np.linalg.inv(cov) for cov in self.covs])

	# @timeit
	def learning(self):
		variance = 0.01
		for ci in range(self.k):
			n = self.pixel_counts[ci]
			if n == 0:
				self.weights[ci] = 0
			else:
				self.weights[ci] = n/self.pixel_total_count
				self.means[ci] = self._sums[ci]/n
				nm = self.means[ci].copy()
				nm.shape = (nm.size, 1)
				self.covs[ci] = self._prods[ci]/n - np.dot(nm, np.transpose(nm))
				self.cov_det[ci] = np.linalg.det(self.covs[ci])
			while self.cov_det[ci] <= 0:
				self.covs[ci] += np.diag([variance for i in range(3)])
				self.cov_det[ci] = np.linalg.det(self.covs[ci])
			self.cov_inv[ci] = np.linalg.inv(self.covs[ci])


class GCClient:
	'''The engine of grabcut'''
	def __init__(self, img, k):
		self.k = k # The number of components in each GMM model

		self.img = np.asarray(img, dtype = np.float32)
		self.img2 = img
		self.rows, self.cols = get_size(img)
		self.gamma = 50
		self.lam = 9*self.gamma
		self.beta = 0

		self._BLUE = [255,0,0]        # rectangle color
		self._RED = [0,0,255]         # PR BG
		self._GREEN = [0,255,0]       # PR FG
		self._BLACK = [0,0,0]         # sure BG
		self._WHITE = [255,255,255]   # sure FG

		self._DRAW_BG = {'color':self._BLACK, 'val':0}
		self._DRAW_FG = {'color':self._WHITE, 'val':1}
		self._DRAW_PR_FG = {'color':self._GREEN, 'val':3}
		self._DRAW_PR_BG = {'color':self._RED, 'val':2}

		# setting up flags
		self._rect = [0, 0, 1, 1]
		self._drawing = False         # flag for drawing curves
		self._rectangle = False       # flag for drawing rect
		self._rect_over = False       # flag to check if rect drawn
		# self._rect_or_mask = 100      # flag for selecting rect or mask mode
		# self._value = DRAW_FG         # drawing initialized to FG
		self._thickness = 3           # brush thickness
		
		self._GC_BGD = 0	#{'color' : BLACK, 'val' : 0}
		self._GC_FGD = 1	#{'color' : WHITE, 'val' : 1}
		self._GC_PR_BGD = 2	#{'color' : GREEN, 'val' : 3}
		self._GC_PR_FGD = 3	#{'color' : RED, 'val' : 2}
		self.calc_beta()
		self.calc_nearby_weight()

		self._DRAW_VAL = None

		self._mask = np.zeros([self.rows, self.cols], dtype = np.uint8) # Init the mask
		self._mask[:, :] = self._GC_BGD


	def calc_beta(self):
		'''Calculate Beta -- The Exp Term of Smooth Parameter in Gibbs Energy'''
		'''beta = 1/(2*average(sqrt(||pixel[i] - pixel[j]||)))'''
		'''Beta is used to adjust the difference of two nearby pixels in high or low contrast rate'''
		beta = 0
		self._left_diff = self.img[:, 1:] - self.img[:, :-1] # Left-difference
		self._upleft_diff = self.img[1:, 1:] - self.img[:-1, :-1] # Up-Left difference
		self._up_diff = self.img[1:, :] - self.img[:-1, :] # Up-difference
		self._upright_diff = self.img[1:, :-1] - self.img[:-1, 1:] # Up-Right difference
		beta = (self._left_diff*self._left_diff).sum() + (self._upleft_diff*self._upleft_diff).sum() \
			+ (self._up_diff*self._up_diff).sum() + (self._upright_diff*self._upright_diff).sum() # According to the formula
		self.beta = 1/(2*beta/(4*self.cols*self.rows - 3*self.cols - 3*self.rows + 2))
		# print(self.beta) # According to the paper

	@timeit
	def calc_nearby_weight(self):
		'''Calculate the weight of the edge of each pixel with its nearby pixel, as each pixel is regarded
			as a vertex of the graph'''
		'''The weight of each direction is saved in a image the same size of the original image'''
		'''weight = gamma*exp(-beta*(diff*diff))'''
		self.left_weight = np.zeros([self.rows, self.cols])
		self.upleft_weight = np.zeros([self.rows, self.cols])
		self.up_weight = np.zeros([self.rows, self.cols])
		self.upright_weight = np.zeros([self.rows, self.cols])
		# Use the formula to calculate the weight
		# for y in range(self.rows):
		# 	for x in range(self.cols):
		# 		color = self.img[y, x]
		# 		if x >= 1:
		# 			diff = color - self.img[y, x-1]
		# 			diff.shape = (1, 3)
		# 			self.left_weight[y, x] = self.gamma*np.exp(-self.beta*np.dot(diff, np.transpose(diff)))
		# 		if x >= 1 and y >= 1:
		# 			diff = color - self.img[y-1, x-1]
		# 			diff.shape = (1, 3)
		# 			self.upleft_weight[y, x] = self.gamma/np.sqrt(2) * np.exp(-self.beta*np.dot(diff, np.transpose(diff)))
		# 		if y >= 1:
		# 			diff = color - self.img[y-1, x]
		# 			diff.shape = (1, 3)
		# 			self.up_weight[y, x] = self.gamma*np.exp(-self.beta*np.dot(diff, np.transpose(diff)))
		# 		if x+1 < self.cols and y >= 1:
		# 			diff = color - self.img[y-1, x+1]
		# 			diff.shape = (1, 3)
		# 			self.upright_weight[y, x] = self.gamma/np.sqrt(2)*np.exp(-self.beta*np.dot(diff, np.transpose(diff)))
		
		# Use the formula to calculate the weight
		for y in range(self.rows):
			for x in range(self.cols):
				color = self.img[y, x]
				if x >= 1:
					diff = color - self.img[y, x-1]
					# print(np.exp(-self.beta*(diff*diff).sum()))
					self.left_weight[y, x] = self.gamma*np.exp(-self.beta*(diff*diff).sum())
				if x >= 1 and y >= 1:
					diff = color - self.img[y-1, x-1]
					self.upleft_weight[y, x] = self.gamma/np.sqrt(2) * np.exp(-self.beta*(diff*diff).sum())
				if y >= 1:
					diff = color - self.img[y-1, x]
					self.up_weight[y, x] = self.gamma*np.exp(-self.beta*(diff*diff).sum())
				if x+1 < self.cols and y >= 1:
					diff = color - self.img[y-1, x+1]
					self.upright_weight[y, x] = self.gamma/np.sqrt(2)*np.exp(-self.beta*(diff*diff).sum())
		

	# @timeit
	def init_with_kmeans(self):
		print(self.cols*self.rows)
		print(len(list(np.where(self._mask == 0))[1]))
		'''Initialise the BGDGMM and FGDGMM, which are respectively background-model and foreground-model,
			using kmeans algorithm'''
		max_iter = 2 # Max-iteration count for Kmeans
		'''In the following two indexings, the np.logical_or is needed in place of or'''
		self._bgd = np.where(np.logical_or(self._mask == self._GC_BGD, self._mask == self._GC_PR_BGD)) # Find the places where pixels in the mask MAY belong to BGD.
		self._fgd = np.where(np.logical_or(self._mask == self._GC_FGD, self._mask == self._GC_PR_FGD)) # Find the places where pixels in the mask MAY belong to FGD.
		self._BGDpixels = self.img[self._bgd]
		self._FGDpixels = self.img[self._fgd]
		KMB = kmeans(self._BGDpixels, dim = 3, n = self.k, max_iter = max_iter) # The Background Model by kmeans
		KMF = kmeans(self._FGDpixels, dim = 3, n = self.k, max_iter = max_iter) # The Foreground Model by kmeans
		KMB.run()
		KMF.run()
		# self._BGD_types = KMB.output()
		# self._FGD_types = KMF.output()
		# print(self._BGD_types)
		self._BGD_by_components = KMB.output()
		self._FGD_by_components = KMF.output()
		self.BGD_GMM = GMM() # The GMM Model for BGD
		self.FGD_GMM = GMM() # The GMM Model for FGD
		'''Add the pixels by components to GMM'''
		for ci in range(self.k):
			# print(len(self._BGD_by_components[ci]))
			# print(self._BGD_by_components[ci])
			for pixel in self._BGD_by_components[ci]:
				# pixel = np.asarray([j for j in pixel], dtype = np.float32)
				self.BGD_GMM.add_pixel(pixel, ci)
			for pixel in self._FGD_by_components[ci]:
				self.FGD_GMM.add_pixel(pixel, ci)
		# for ci in range(self.k):
		# 	bgd_index = np.where(self._BGD_types == ci)
		# 	fgd_index = np.where(self._FGD_types == ci)
		# 	for pixel in self.img[bgd_index]:
		# 		self.BGD_GMM.add_pixel(pixel, ci)
		# 	for pixel in self.img[fgd_index]:
		# 		self.FGD_GMM.add_pixel(pixel, ci)
		self.BGD_GMM.learning()
		self.FGD_GMM.learning()

	'''The first step of the iteration in the paper: Assign components of GMMs to pixels,
		(the kn in the paper), which is saved in self.components_index'''
	# @timeit
	def assign_GMM_components(self):
		self.components_index = np.zeros([self.rows, self.cols], dtype = np.uint)
		# self.components_index[self._bgd] = [i[0] for i in self.BGD_GMM.vec_pix_comp(self.img[self._bgd])]
		# self.components_index[self._fgd] = [i[0] for i in self.FGD_GMM.vec_pix_comp(self.img[self._fgd])]
		for y in range(self.rows):
			for x in range(self.cols):
				pixel = self.img[y, x]
				self.components_index[y, x] = self.BGD_GMM.most_likely_pixel_component(pixel) if (self._mask[y, x] \
					== self._GC_BGD or self._mask[y, x] == self._GC_PR_BGD) else self.FGD_GMM.most_likely_pixel_component(pixel)

	# @timeit
	def _assign_GMM_components(self):
		self.components_index = np.zeros([self.rows, self.cols], dtype = np.uint)
		self.components_index[self._bgd] = [i[0] for i in self.BGD_GMM.vec_pix_comp(self.img[self._bgd])]
		self.components_index[self._fgd] = [i[0] for i in self.FGD_GMM.vec_pix_comp(self.img[self._fgd])]



	'''The second step in the iteration: Learn the parameters from GMM models'''
	# @timeit
	def learn_GMM_parameters(self):
		for ci in range(self.k):
			# The places where the pixel belongs to the ci_th model and background model.
			bgd_ci = np.where(np.logical_and(self.components_index == ci, np.logical_or(self._mask == self._GC_BGD, self._mask == self._GC_PR_BGD)))
			fgd_ci = np.where(np.logical_and(self.components_index == ci, np.logical_or(self._mask == self._GC_FGD, self._mask == self._GC_PR_FGD)))
			for pixel in self.img[bgd_ci]:
				self.BGD_GMM.add_pixel(pixel, ci)
			for pixel in self.img[fgd_ci]:
				self.FGD_GMM.add_pixel(pixel, ci)
		self.BGD_GMM.learning()
		self.FGD_GMM.learning()

	# @timeit
	def construct_gcgraph(self, lam):
		'''Construct a GCGraph with the Gibbs Energy'''
		'''The vertexs of the graph are the pixels, and the edges are constructed by two parts,
			the first part of which are the edges that connect each vertex with Sink Point(the background) and the Source Point(the foreground),
			and the weight of which is the first term in Gibbs Energy;
			the second part of the edges are those that connect each vertex with its neighbourhoods,
			and the weight of which is the second term in Gibbs Energy.'''
		vertex_count = self.cols*self.rows
		edge_count = 2*(4*vertex_count - 3*(self.rows + self.cols) + 2)
		self.graph = GCGraph(vertex_count, edge_count)
		for y in range(self.rows):
			for x in range(self.cols):
				vertex_index = self.graph.add_vertex() # add-node and return its index
				color = self.img[y, x]
				# '''Set t-weights: Calculate the weight of each vertex with Sink node and Source node'''
				if self._mask[y, x] == self._GC_PR_BGD or self._mask[y, x] == self._GC_PR_FGD:
					# For each vertex, calculate the first term of G.E. as it be the BGD or FGD, and set them respectively as weight to t/s.
					fromSource = -np.log(self.BGD_GMM.prob_pixel_GMM(color))
					toSink = -np.log(self.FGD_GMM.prob_pixel_GMM(color))
					# print(np.exp(-fromSource), np.exp(-toSink))
					# print(fromSource)
				elif self._mask[y, x] == self._GC_BGD:
					# For the vertexs that are Background pixels, t-weight with Source = 0, with Sink = lam
					fromSource = 0
					toSink = lam
				else:
					# GC_FGD
					fromSource = lam
					toSink = 0
				# print(fromSource, toSink)
				self.graph.add_term_weights(vertex_index, fromSource, toSink)

				'''Set n-weights and n-link, Calculate the weights between two neighbour vertexs, which is also the second term in Gibbs Energy(the smooth term)'''
				if x > 0:
					w = self.left_weight[y, x]
					self.graph.add_edges(vertex_index, vertex_index-1, w, w)
				if x > 0 and y > 0:
					w = self.upleft_weight[y, x]
					self.graph.add_edges(vertex_index, vertex_index-self.cols-1, w, w)
				if y > 0:
					w = self.up_weight[y, x]
					self.graph.add_edges(vertex_index, vertex_index-self.cols, w, w)
				if x < self.cols - 1 and y > 0:
					w = self.upright_weight[y, x]
					self.graph.add_edges(vertex_index, vertex_index-self.cols+1, w, w)

	# @timeit
	def estimate_segmentation(self):
		a =  self.graph.max_flow()
		for y in range(self.rows):
			for x in range(self.cols):
				if self._mask[y, x] == self._GC_PR_BGD or self._mask[y, x] == self._GC_PR_FGD:
					if self.graph.insource_segment(y*self.cols+x): # Vertex Index
						self._mask[y, x] = self._GC_PR_FGD
					else:
						# print(y, x)
						self._mask[y, x] = self._GC_PR_BGD

	def iter(self, n):
		for i in range(n):
			self.assign_GMM_components()
			self.learn_GMM_parameters()
			self.construct_gcgraph(self.lam)
			self.estimate_segmentation()
			# self._smoothing()

	def run(self):
		self.init_with_kmeans()
		self.iter(1)

	def _smoothing(self):
		for y in range(1, self.rows-2):
			for x in range(1, self.cols-2):
				# if self._mask[x-1, y] == self._mask[x+1, y] == self._mask[x, y-1] == self._mask[x, y+1]:
				a = self._mask[x-1, y]
				b = self._mask[x+1, y]
				c = self._mask[x, y-1]
				d = self._mask[x, y+1]
				if a==b==3 or a==c==3 or a==d==3 or b==c==3 or b==d==3 or c==d==3:
					self._mask[x, y] = 3

	def show(self, output):
		# 
		# FGD = np.where(np.logical_and(np.logical_or(self._mask == 1, self._mask == 3), self._mask0 == 3))
		# FGD = np.where(np.logical_or(self._mask==1, self._mask==3))
		FGD = np.where((self._mask == 1) + (self._mask == 3), 255, 0).astype('uint8')
		# output[FGD] = self.img[FGD]
		# output = output.astype(np.uint8)
		output = cv2.bitwise_and(self.img2, self.img2, mask = FGD)
		# print('Press N to continue')
		return output

	# def update_mask_by_user(self):
		



if __name__ == '__main__':

	print('go!')
