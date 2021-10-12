myArray = ["+", 100, "-", 50, "+", 100, "-", 144]

def myFunc(array):
    count = 0
    for n in range(0, len(array)):
        antiZero = n + 1
        if antiZero % 2 == 0:
            operator = array[n - 1]
            if operator == "+":
                count = count + array[n]
            else:
                count = count - array[n]
    return count

print(myFunc(myArray))