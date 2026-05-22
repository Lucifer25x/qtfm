import heapq
import pickle
import datetime
import os
from collections import Counter
from bitarray import bitarray

class HuffmanNode:
  def __init__(self, char, freq):
    self.char = char
    self.freq = freq
    self.left = None
    self.right = None
  
  def __lt__(self, other):
    return self.freq < other.freq
  
def build_tree(text):
  freqs = Counter(text)
  heap = [HuffmanNode(char, f) for char, f in freqs.items()]
  heapq.heapify(heap)

  while len(heap) > 1:
    node1 = heapq.heappop(heap)
    node2 = heapq.heappop(heap)
    merged = HuffmanNode(None, node1.freq + node2.freq)
    merged.left = node1
    merged.right = node2
    heapq.heappush(heap, merged)
  return heap[0]

def build_codes(node, current_code, codes):
  if node is None:
    return
  if node.char is not None:
    codes[node.char] = current_code
  build_codes(node.left, current_code + "0", codes)
  build_codes(node.right, current_code + "1", codes)

def compress(file_path):
  with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

  if not text:
    raise ValueError("Cannot compress the file.")

  root = build_tree(text)
  codes = {}
  build_codes(root, "", codes)

  bit_codes = {char: bitarray(code) for char, code in codes.items()}
  encoded_bits = bitarray()
  encoded_bits.encode(bit_codes, text)

  output_path = file_path + '.huff'
  if os.path.exists(output_path):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_path = f"{file_path}_{timestamp}.huff"
  with open(output_path, 'wb') as f:
    pickle.dump(codes, f)
    pickle.dump(len(encoded_bits), f)
    encoded_bits.tofile(f)
  
  return output_path

def decompress(file_path):
  if not file_path.endswith('.huff'):
    raise ValueError("The file does not have a .huff extension.")
  if os.path.getsize(file_path) == 0:
    raise ValueError("The file is empty and cannot be decompressed.")
  with open(file_path, 'rb') as f:
    codes = pickle.load(f)
    target_bits_length = pickle.load(f)
    encoded_bits = bitarray()
    encoded_bits.fromfile(f)
    encoded_bits = encoded_bits[:target_bits_length]
  
  bit_codes = {char: bitarray(code) for char, code in codes.items()}
  decoded_list = encoded_bits.decode(bit_codes)
  decoded_text = ''.join(decoded_list)

  output_path = file_path.replace('.huff', '_decompressed.txt')
  if os.path.exists(output_path):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_path = f"{file_path.replace('.huff', '')}_{timestamp}_decompressed.txt"
  with open(output_path, 'w', encoding='utf-8') as f:
    f.write(decoded_text)
  
  return output_path

def main():
  method = input("Enter 'c' to compress or 'd' to decompress: ").strip().lower()
  file_path = input("Enter the file path: ").strip()
  if method == 'c':
    output = compress(file_path)
    print(f"File compressed to: {output}")
  elif method == 'd':
    output = decompress(file_path)
    print(f"File decompressed to: {output}")
  else:
    print("Invalid option. Please enter 'c' or 'd'.")

if __name__ == "__main__":
  main()