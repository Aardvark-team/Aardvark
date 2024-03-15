# This file removes the nltk dependency.


def edit_distance(word1, word2):
    # Get the lengths of the two words.
    m = len(word1)
    n = len(word2)

    # Create a 2D array to store the dynamic programming table.
    dp = [[0 for _ in range(n + 1)] for _ in range(m + 1)]

    # Initialize the first row and column of the DP table.
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    # Fill in the DP table.
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            # Calculate the cost of substitution (0 if characters are the same, 1 otherwise).
            cost = 0 if word1[i - 1] == word2[j - 1] else 1

            # Use the minimum of three possible operations: deletion, insertion, or substitution.
            dp[i][j] = min(
                dp[i - 1][j] + 1,  # Deletion
                dp[i][j - 1] + 1,  # Insertion
                dp[i - 1][j - 1] + cost,  # Substitution
            )

    # The final value in the DP table represents the edit distance between the two words.
    return dp[m][n]
