
2025-09-05

Brock & Jason over at Brock's house. Worked through the problem. It is pretty difficult to decompose into separate pieces, so we've mostly talked through strategies and on paper brainstormed different ways to visualize. Jason came up with an idea to identify rooms based on their "fingerprint" which is their label and the labels of all of the adjoining rooms. Brock then used this concept to systematically verify every connection. It won't work if there is true ambiguity, but seems like it might work for the lightning-round problems.

2025-09-05 21:17 Fri - Now submitting 5 at a time

This should decrease the cost a lot, as each API call loses a point.

2025-09-06 09:31 Sat - Reading up on the post-lighting info

Yesterday we got it working doing systematic exploration of rooms, and used that to solve all of the problems -- nabbing a top-30 ranking (at least temporarily). It seems like the thing we are missing is doing LONG chains of exploration, which have no penalty but then are harder to analyze.

Today the ambiguity of the rooms has increased, but they gave us the ability to overwrite the labels with our own (still 0..3). So like you could change all the labels to 0 as you go, and then if you see a label-0 then you can be suspicious, or something.

