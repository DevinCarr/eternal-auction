class Herbs:
    def __init__(self, N, D, R, M, W, V):
        self.N = N
        self.D = D
        self.R = R
        self.M = M
        self.W = W
        self.V = V

def cauldron(herbs):
    '''
    Eternal Cauldron:
	8 Flasks
	2 Shadestone
    '''
    return 8 * flask(herbs) + 2 * shadestone(herbs)

def flask(herbs):
    '''
    Flask:
	3 Nightshade
	4 Rising Glory
	4 Marrowroot
	4 Widowbloom
	4 Vigil's Torch
    '''
    return 3 * herbs.N + 4 * (herbs.R + herbs.M + herbs.W + herbs.V)

def shadestone(herbs):
    '''
    Shadestone:
	5 Ground Death Blossom
	2 Ground Vigil's Torch
	2 Ground Widowbloom
	2 Ground Marrowroot
	2 Ground Rising Glory
    Ground: 2 * herb
    '''
    return 2 * (5 * herbs.D + 2 * (herbs.V + herbs.W + herbs.M + herbs.R))

def main():
    herbs = Herbs(N = 139, D = 39, R = 36, M = 110, W = 195, V = 115)
    print(cauldron(herbs))

if __name__ == "__main__":
    main()
