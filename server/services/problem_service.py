"""Curated interview problems with LeetCode as the live source of truth."""

from __future__ import annotations

import json
import random
import re
from html import unescape
from urllib.error import URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field

RANDOM_PROBLEM_SLUG = "random-amazon-sde1"


class GroundedProblem(BaseModel):
    id: str
    slug: str
    source: str
    title: str
    difficulty: str
    description: str
    constraints: list[str] = Field(default_factory=list)
    examples: list[dict] = Field(default_factory=list)
    time_target: str = "Discuss with interviewer"
    space_target: str = "Discuss with interviewer"


_FALLBACK: dict[str, GroundedProblem] = {
    "two-sum": GroundedProblem(
        id="1",
        slug="two-sum",
        source="leetcode",
        title="Two Sum",
        difficulty="Easy",
        description=(
            "Given an array of integers nums and an integer target, return the indices of the "
            "two numbers that add up to target. You may assume that each input has exactly one "
            "solution, and you may not use the same element twice."
        ),
        constraints=[
            "2 <= nums.length <= 10^4",
            "-10^9 <= nums[i], target <= 10^9",
            "Exactly one valid answer exists.",
        ],
        examples=[
            {
                "input": "nums = [2,7,11,15], target = 9",
                "output": "[0,1]",
                "explanation": "nums[0] + nums[1] equals 9.",
            }
        ],
        time_target="O(n)",
        space_target="O(n)",
    ),
    "valid-palindrome": GroundedProblem(
        id="125",
        slug="valid-palindrome",
        source="leetcode",
        title="Valid Palindrome",
        difficulty="Easy",
        description=(
            "A phrase is a palindrome if, after converting uppercase letters to lowercase and "
            "removing non-alphanumeric characters, it reads the same forward and backward. "
            "Given a string s, return true if it is a palindrome, or false otherwise."
        ),
        constraints=[
            "1 <= s.length <= 2 * 10^5",
            "s consists only of printable ASCII characters.",
        ],
        examples=[
            {
                "input": 's = "A man, a plan, a canal: Panama"',
                "output": "true",
                "explanation": 'After normalization, the string is "amanaplanacanalpanama".',
            }
        ],
        time_target="O(n)",
        space_target="O(1)",
    ),
    "reverse-linked-list": GroundedProblem(
        id="206",
        slug="reverse-linked-list",
        source="leetcode",
        title="Reverse Linked List",
        difficulty="Easy",
        description="Given the head of a singly linked list, reverse the list and return its new head.",
        constraints=[
            "The number of nodes is in the range [0, 5000].",
            "-5000 <= Node.val <= 5000",
        ],
        examples=[{"input": "head = [1,2,3,4,5]", "output": "[5,4,3,2,1]"}],
        time_target="O(n)",
        space_target="O(1)",
    ),
    "merge-intervals": GroundedProblem(
        id="56",
        slug="merge-intervals",
        source="leetcode",
        title="Merge Intervals",
        difficulty="Medium",
        description=(
            "Given an array of intervals where intervals[i] = [start_i, end_i], merge all "
            "overlapping intervals and return an array of the non-overlapping intervals that "
            "cover all the intervals in the input."
        ),
        constraints=[
            "1 <= intervals.length <= 10^4",
            "intervals[i].length == 2",
            "0 <= start_i <= end_i <= 10^4",
        ],
        examples=[
            {
                "input": "intervals = [[1,3],[2,6],[8,10],[15,18]]",
                "output": "[[1,6],[8,10],[15,18]]",
                "explanation": "[1,3] and [2,6] overlap, so they merge into [1,6].",
            }
        ],
        time_target="O(n log n)",
        space_target="O(n)",
    ),
    "best-time-to-buy-and-sell-stock": GroundedProblem(
        id="121",
        slug="best-time-to-buy-and-sell-stock",
        source="leetcode",
        title="Best Time to Buy and Sell Stock",
        difficulty="Easy",
        description=(
            "Given prices where prices[i] is the price of a stock on day i, choose one day to "
            "buy and a later day to sell. Return the maximum profit, or 0 if no profitable "
            "transaction is possible."
        ),
        constraints=["1 <= prices.length <= 10^5", "0 <= prices[i] <= 10^4"],
        examples=[
            {
                "input": "prices = [7,1,5,3,6,4]",
                "output": "5",
                "explanation": "Buy at 1 and sell later at 6 for a profit of 5.",
            }
        ],
        time_target="O(n)",
        space_target="O(1)",
    ),
    "contains-duplicate": GroundedProblem(
        id="217",
        slug="contains-duplicate",
        source="leetcode",
        title="Contains Duplicate",
        difficulty="Easy",
        description="Given an integer array nums, return true if any value appears at least twice, and false if every element is distinct.",
        constraints=["1 <= nums.length <= 10^5", "-10^9 <= nums[i] <= 10^9"],
        examples=[
            {
                "input": "nums = [1,2,3,1]",
                "output": "true",
                "explanation": "The value 1 appears at indices 0 and 3.",
            }
        ],
        time_target="O(n)",
        space_target="O(n)",
    ),
    "valid-parentheses": GroundedProblem(
        id="20",
        slug="valid-parentheses",
        source="leetcode",
        title="Valid Parentheses",
        difficulty="Easy",
        description=(
            "Given a string s containing only '(', ')', '{', '}', '[' and ']', determine if "
            "the input string is valid. Open brackets must be closed by the same type of "
            "bracket in the correct order."
        ),
        constraints=["1 <= s.length <= 10^4", "s contains only bracket characters."],
        examples=[{"input": 's = "()[]{}"', "output": "true"}],
        time_target="O(n)",
        space_target="O(n)",
    ),
    "merge-two-sorted-lists": GroundedProblem(
        id="21",
        slug="merge-two-sorted-lists",
        source="leetcode",
        title="Merge Two Sorted Lists",
        difficulty="Easy",
        description=(
            "You are given the heads of two sorted linked lists. Merge them into one sorted "
            "linked list by reusing the existing nodes and return its head."
        ),
        constraints=[
            "The number of nodes in both lists is in the range [0, 50].",
            "-100 <= Node.val <= 100",
            "Both lists are sorted in non-decreasing order.",
        ],
        examples=[
            {
                "input": "list1 = [1,2,4], list2 = [1,3,4]",
                "output": "[1,1,2,3,4,4]",
            }
        ],
        time_target="O(n + m)",
        space_target="O(1)",
    ),
    "binary-search": GroundedProblem(
        id="704",
        slug="binary-search",
        source="leetcode",
        title="Binary Search",
        difficulty="Easy",
        description=(
            "Given a sorted array of distinct integers nums and a target value, return the "
            "index of target if it exists. Otherwise, return -1."
        ),
        constraints=[
            "1 <= nums.length <= 10^4",
            "-10^4 < nums[i], target < 10^4",
            "All integers in nums are unique.",
            "nums is sorted in ascending order.",
        ],
        examples=[
            {
                "input": "nums = [-1,0,3,5,9,12], target = 9",
                "output": "4",
            }
        ],
        time_target="O(log n)",
        space_target="O(1)",
    ),
    "maximum-subarray": GroundedProblem(
        id="53",
        slug="maximum-subarray",
        source="leetcode",
        title="Maximum Subarray",
        difficulty="Medium",
        description="Given an integer array nums, find the subarray with the largest sum and return that sum. A subarray is a contiguous non-empty sequence of elements.",
        constraints=["1 <= nums.length <= 10^5", "-10^4 <= nums[i] <= 10^4"],
        examples=[
            {
                "input": "nums = [-2,1,-3,4,-1,2,1,-5,4]",
                "output": "6",
                "explanation": "The subarray [4,-1,2,1] has the largest sum, 6.",
            }
        ],
        time_target="O(n)",
        space_target="O(1)",
    ),
    "group-anagrams": GroundedProblem(
        id="49",
        slug="group-anagrams",
        source="leetcode",
        title="Group Anagrams",
        difficulty="Medium",
        description="Given an array of strings strs, group the anagrams together. You may return the answer in any order.",
        constraints=[
            "1 <= strs.length <= 10^4",
            "0 <= strs[i].length <= 100",
            "strs[i] consists of lowercase English letters.",
        ],
        examples=[
            {
                "input": 'strs = ["eat","tea","tan","ate","nat","bat"]',
                "output": '[["bat"],["nat","tan"],["ate","eat","tea"]]',
            }
        ],
        time_target="O(n k)",
        space_target="O(n k)",
    ),
    "product-of-array-except-self": GroundedProblem(
        id="238",
        slug="product-of-array-except-self",
        source="leetcode",
        title="Product of Array Except Self",
        difficulty="Medium",
        description="Given an integer array nums, return an array answer where answer[i] is the product of every element of nums except nums[i]. Do not use division, and aim for O(1) extra space excluding the output array.",
        constraints=["2 <= nums.length <= 10^5", "-30 <= nums[i] <= 30", "The product of any prefix or suffix fits in a 32-bit integer."],
        examples=[
            {
                "input": "nums = [1,2,3,4]",
                "output": "[24,12,8,6]",
            }
        ],
        time_target="O(n)",
        space_target="O(1) extra, excluding output",
    ),
    "number-of-islands": GroundedProblem(
        id="200",
        slug="number-of-islands",
        source="leetcode",
        title="Number of Islands",
        difficulty="Medium",
        description="Given an m x n grid of '1's (land) and '0's (water), count the number of islands. An island is formed by connecting adjacent land cells horizontally or vertically and is surrounded by water.",
        constraints=["1 <= m, n <= 300", "grid[i][j] is either '0' or '1'."],
        examples=[
            {
                "input": 'grid = [["1","1","1","1","0"],["1","1","0","1","0"],["1","1","0","0","0"],["0","0","0","0","0"]]',
                "output": "1",
            }
        ],
        time_target="O(m n)",
        space_target="O(m n) worst case",
    ),
    "longest-substring-without-repeating-characters": GroundedProblem(
        id="3",
        slug="longest-substring-without-repeating-characters",
        source="leetcode",
        title="Longest Substring Without Repeating Characters",
        difficulty="Medium",
        description="Given a string s, find the length of the longest substring without repeating characters.",
        constraints=["0 <= s.length <= 5 * 10^4", "s consists of English letters, digits, symbols, and spaces."],
        examples=[
            {
                "input": 's = "abcabcbb"',
                "output": "3",
                "explanation": 'The answer is "abc", with length 3.',
            }
        ],
        time_target="O(n)",
        space_target="O(min(n, character set))",
    ),
    "top-k-frequent-elements": GroundedProblem(
        id="347",
        slug="top-k-frequent-elements",
        source="leetcode",
        title="Top K Frequent Elements",
        difficulty="Medium",
        description="Given an integer array nums and an integer k, return the k most frequent elements. The answer may be returned in any order.",
        constraints=["1 <= nums.length <= 10^5", "-10^4 <= nums[i] <= 10^4", "k is between 1 and the number of distinct values."],
        examples=[{"input": "nums = [1,1,1,2,2,3], k = 2", "output": "[1,2]"}],
        time_target="O(n)",
        space_target="O(n)",
    ),
}

# Two Sum remains available by explicit selection, but is excluded from the
# random mock pool so a fresh interview is not repeatedly grounded on it.
_RANDOM_POOL = tuple(slug for slug in _FALLBACK if slug != "two-sum")


def _strip_html(value: str) -> str:
    return unescape(re.sub(r"<[^>]+>", " ", value)).replace("\xa0", " ").strip()


def fetch_leetcode_problem(title_slug: str) -> GroundedProblem:
    slug = title_slug.strip().lower().strip("/")
    if not slug:
        raise ValueError("A LeetCode problem slug is required.")

    fallback = _FALLBACK.get(slug)
    query = {
        "query": (
            "query question($titleSlug: String!) { question(titleSlug: $titleSlug) "
            "{ questionId title difficulty content } }"
        ),
        "variables": {"titleSlug": slug},
    }
    try:
        request = Request(
            "https://leetcode.com/graphql",
            data=json.dumps(query).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "PrepareIt/1.0 (interview practice)",
            },
            method="POST",
        )
        with urlopen(request, timeout=8) as response:
            payload = json.load(response)
        question = payload.get("data", {}).get("question") or {}
        if question.get("title"):
            return GroundedProblem(
                id=str(question.get("questionId") or (fallback.id if fallback else slug)),
                slug=slug,
                source="leetcode",
                title=question["title"],
                difficulty=question.get("difficulty") or (fallback.difficulty if fallback else "Unknown"),
                description=_strip_html(question.get("content") or "")
                or (fallback.description if fallback else ""),
                constraints=fallback.constraints if fallback else [],
                examples=fallback.examples if fallback else [],
                time_target=fallback.time_target if fallback else "Discuss with interviewer",
                space_target=fallback.space_target if fallback else "Discuss with interviewer",
            )
    except (OSError, URLError, ValueError, KeyError, TypeError):
        pass

    if fallback:
        return fallback.model_copy(update={"slug": slug})
    raise ValueError(
        f"LeetCode problem '{slug}' could not be loaded. Check the slug or choose a problem from the interview pool."
    )


class ProblemService:
    @staticmethod
    def catalog() -> list[dict[str, str]]:
        """Return UI options for the random mock and every curated problem."""
        options = [
            {
                "slug": RANDOM_PROBLEM_SLUG,
                "title": "Random Amazon SDE I",
                "difficulty": "Easy / Medium",
                "source": "leetcode",
            }
        ]
        options.extend(
            {
                "slug": problem.slug,
                "title": problem.title,
                "difficulty": problem.difficulty,
                "source": problem.source,
            }
            for slug, problem in _FALLBACK.items()
            if slug != RANDOM_PROBLEM_SLUG
        )
        return options

    @staticmethod
    def fetch_codeforces_problem(contest_id: str, index: str) -> GroundedProblem:
        slug = f"cf-{contest_id}-{index}".lower()
        try:
            request = Request(
                f"https://codeforces.com/api/problemset.problem?contestId={contest_id}&index={index}",
                headers={"User-Agent": "PrepareIt/1.0 (interview practice)"},
            )
            with urlopen(request, timeout=8) as response:
                result = json.load(response).get("result", {}).get("problems", [])
            if result:
                item = result[0]
                return GroundedProblem(
                    id=slug,
                    slug=slug,
                    source="codeforces",
                    title=item.get("name", f"Codeforces {contest_id}{index}"),
                    difficulty=str(item.get("rating", "Unknown")),
                    description="Use the interviewer-provided statement for this Codeforces problem.",
                )
        except (OSError, URLError, ValueError, KeyError, TypeError):
            pass
        raise ValueError(f"Codeforces problem {contest_id}{index} could not be loaded.")

    @staticmethod
    def fetch(slug: str) -> GroundedProblem:
        normalized = slug.strip().lower().strip("/")
        if not normalized:
            raise ValueError("A problem slug is required.")
        if normalized == RANDOM_PROBLEM_SLUG:
            normalized = random.choice(_RANDOM_POOL)
        if normalized.startswith("cf-"):
            parts = normalized.split("-", 2)
            if len(parts) != 3 or not parts[1] or not parts[2]:
                raise ValueError("Use a Codeforces slug in the form cf-<contest>-<index>.")
            return ProblemService.fetch_codeforces_problem(parts[1], parts[2])
        return fetch_leetcode_problem(normalized)
