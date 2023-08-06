import numpy
import json

negativeEmbedding = numpy.load('D:/projects/ica_trial/static/models/pushup-pose_II/negative-embeddings.npy')
positiveEmbedding = numpy.load('D:/projects/ica_trial/static/models/pushup-pose_II/positive-embeddings.npy')
negativeJson = negativeEmbedding.tolist()
positiveJson = positiveEmbedding.tolist()

with open('negative_embedding.json', 'w') as outfile:
    json.dump(negativeJson, outfile, indent=3)

with open('positive_embedding.json', 'w') as outfile:
    json.dump(positiveJson, outfile, indent=3)