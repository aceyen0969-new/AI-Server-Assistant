#include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include <map>
#include <fstream>
#include <set>
#include <algorithm>
#include <cctype>

struct LanguageSegment {
    std::string language;
    std::vector<std::string> words;
};

std::string normalize(
    const std::string& word
) {
    std::string result;

    for (char character : word) {
        if (
            std::isalnum(
                static_cast<unsigned char>(
                    character
                )
            )
        ) {
            result += static_cast<char>(
                std::tolower(
                    static_cast<unsigned char>(
                        character
                    )
                )
            );
        }
    }

    return result;
}

std::vector<std::string> tokenize(
    const std::string& text
) {
    std::vector<std::string> words;
    std::stringstream stream(text);
    std::string word;

    while (stream >> word) {
        word = normalize(word);

        if (!word.empty()) {
            words.push_back(word);
        }
    }

    return words;
}

std::map<std::string, int> build_trigrams(
    const std::vector<std::string>& words
) {
    std::map<std::string, int> trigrams;

    for (const std::string& word : words) {
        if (word.length() < 3) {
            continue;
        }

        for (
            std::size_t i = 0;
            i + 2 < word.length();
            ++i
        ) {
            std::string trigram =
                word.substr(i, 3);

            trigrams[trigram]++;
        }
    }

    return trigrams;
}

std::map<std::string, double> build_profile(
    const std::vector<std::string>& words
) {
    std::map<std::string, double> profile;

    std::map<std::string, int> trigrams =
        build_trigrams(words);

    int total = 0;

    for (
        const auto& entry : trigrams
    ) {
        total += entry.second;
    }

    if (total == 0) {
        return profile;
    }

    for (
        const auto& entry : trigrams
    ) {
        profile[entry.first] =
            static_cast<double>(
                entry.second
            ) /
            static_cast<double>(
                total
            );
    }

    return profile;
}

void merge_profile(
    std::map<std::string, double>& target,
    const std::map<std::string, double>& source
) {
    for (
        const auto& entry : source
    ) {
        target[entry.first] +=
            entry.second;
    }
}

std::set<std::string> build_vocabulary(
    const std::vector<std::string>& words
) {
    std::set<std::string> vocabulary;

    for (
        const std::string& word : words
    ) {
        std::string normalized =
            normalize(word);

        if (!normalized.empty()) {
            vocabulary.insert(
                normalized
            );
        }
    }

    return vocabulary;
}

void merge_vocabulary(
    std::set<std::string>& target,
    const std::set<std::string>& source
) {
    target.insert(
        source.begin(),
        source.end()
    );
}

int count_vocabulary_matches(
    const std::vector<std::string>& words,
    const std::set<std::string>& vocabulary
) {
    int count = 0;

    for (
        const std::string& word : words
    ) {
        if (
            vocabulary.find(word)
            != vocabulary.end()
        ) {
            count++;
        }
    }

    return count;
}

int count_unique_vocabulary_matches(
    const std::vector<std::string>& words,
    const std::set<std::string>& vocabulary,
    const std::set<std::string>& other_vocabulary_1,
    const std::set<std::string>& other_vocabulary_2
) {
    int count = 0;

    for (
        const std::string& word : words
    ) {
        bool in_current =
            vocabulary.find(word)
            != vocabulary.end();

        bool in_other_1 =
            other_vocabulary_1.find(word)
            != other_vocabulary_1.end();

        bool in_other_2 =
            other_vocabulary_2.find(word)
            != other_vocabulary_2.end();

        if (
            in_current &&
            !in_other_1 &&
            !in_other_2
        ) {
            count++;
        }
    }

    return count;
}

double calculate_trigram_score(
    const std::string& word,
    const std::map<std::string, double>& profile
) {
    if (word.length() < 3) {
        return 0.0;
    }

    double score = 0.0;

    int trigram_count = 0;

    for (
        std::size_t i = 0;
        i + 2 < word.length();
        ++i
    ) {
        std::string trigram =
            word.substr(i, 3);

        auto found =
            profile.find(trigram);

        if (
            found != profile.end()
        ) {
            score += found->second;
        }

        trigram_count++;
    }

    if (trigram_count == 0) {
        return 0.0;
    }

    return score /
        static_cast<double>(
            trigram_count
        );
}

double calculate_score_margin(
    double highest,
    double second_highest
) {
    if (highest <= 0.0) {
        return 0.0;
    }

    return (
        highest - second_highest
    ) / highest;
}

bool detect_code_switch(
    int english_unique_score,
    int filipino_unique_score,
    int bisaya_unique_score
) {
    int language_count = 0;

    if (
        english_unique_score >= 1
    ) {
        language_count++;
    }

    if (
        filipino_unique_score >= 1
    ) {
        language_count++;
    }

    if (
        bisaya_unique_score >= 1
    ) {
        language_count++;
    }

    return language_count >= 2;
}

std::string word_language(
    const std::string& word,
    const std::set<std::string>& english_vocabulary,
    const std::set<std::string>& filipino_vocabulary,
    const std::set<std::string>& bisaya_vocabulary,
    const std::map<std::string, double>& english_profile,
    const std::map<std::string, double>& filipino_profile,
    const std::map<std::string, double>& bisaya_profile
) {
    bool english =
        english_vocabulary.find(word)
        != english_vocabulary.end();

    bool filipino =
        filipino_vocabulary.find(word)
        != filipino_vocabulary.end();

    bool bisaya =
        bisaya_vocabulary.find(word)
        != bisaya_vocabulary.end();

    int language_matches =
        static_cast<int>(english) +
        static_cast<int>(filipino) +
        static_cast<int>(bisaya);

    if (language_matches == 1) {
        if (english) {
            return "english";
        }

        if (filipino) {
            return "filipino";
        }

        return "bisaya";
    }

    std::vector<
        std::pair<std::string, double>
    > scores = {
        {
            "english",
            calculate_trigram_score(
                word,
                english_profile
            )
        },
        {
            "filipino",
            calculate_trigram_score(
                word,
                filipino_profile
            )
        },
        {
            "bisaya",
            calculate_trigram_score(
                word,
                bisaya_profile
            )
        }
    };

    std::sort(
        scores.begin(),
        scores.end(),
        [](
            const auto& a,
            const auto& b
        ) {
            return a.second > b.second;
        }
    );

    double highest =
        scores[0].second;

    double second_highest =
        scores[1].second;

    double total =
        scores[0].second +
        scores[1].second +
        scores[2].second;

    if (highest <= 0.0) {
        return "unknown";
    }

    double confidence =
        highest / total;

    double relative_margin =
        calculate_score_margin(
            highest,
            second_highest
        );

    if (
        confidence < 0.20 ||
        relative_margin < 0.10
    ) {
        return "shared";
    }

    return scores[0].first;
}

std::vector<std::string> collect_unknown_words(
    const std::vector<std::string>& words,
    const std::set<std::string>& english_vocabulary,
    const std::set<std::string>& filipino_vocabulary,
    const std::set<std::string>& bisaya_vocabulary,
    const std::map<std::string, double>& english_profile,
    const std::map<std::string, double>& filipino_profile,
    const std::map<std::string, double>& bisaya_profile
) {
    std::vector<std::string> unknown_words;

    for (
        const std::string& word : words
    ) {
        std::string language =
            word_language(
                word,
                english_vocabulary,
                filipino_vocabulary,
                bisaya_vocabulary,
                english_profile,
                filipino_profile,
                bisaya_profile
            );

        if (
            language == "unknown" ||
            language == "shared"
        ) {
            if (
                std::find(
                    unknown_words.begin(),
                    unknown_words.end(),
                    word
                ) == unknown_words.end()
            ) {
                unknown_words.push_back(
                    word
                );
            }
        }
    }

    return unknown_words;
}

std::vector<LanguageSegment>
build_language_segments(
    const std::vector<std::string>& words,
    const std::set<std::string>& english_vocabulary,
    const std::set<std::string>& filipino_vocabulary,
    const std::set<std::string>& bisaya_vocabulary,
    const std::map<std::string, double>& english_profile,
    const std::map<std::string, double>& filipino_profile,
    const std::map<std::string, double>& bisaya_profile
) {
    std::vector<LanguageSegment> segments;

    LanguageSegment current;
    bool has_current = false;

    for (
        const std::string& word : words
    ) {
        std::string language =
            word_language(
                word,
                english_vocabulary,
                filipino_vocabulary,
                bisaya_vocabulary,
                english_profile,
                filipino_profile,
                bisaya_profile
            );

        if (
            language == "unknown" ||
            language == "shared"
        ) {
            continue;
        }

        if (
            !has_current ||
            current.language != language
        ) {
            if (has_current) {
                segments.push_back(
                    current
                );
            }

            current.language =
                language;

            current.words.clear();

            has_current = true;
        }

        current.words.push_back(
            word
        );
    }

    if (has_current) {
        segments.push_back(
            current
        );
    }

    return segments;
}

int count_language_switches(
    const std::vector<LanguageSegment>& segments
) {
    if (segments.size() <= 1) {
        return 0;
    }

    return static_cast<int>(
        segments.size() - 1
    );
}

std::string build_switch_direction(
    const std::vector<LanguageSegment>& segments
) {
    if (segments.empty()) {
        return "none";
    }

    std::string direction =
        segments[0].language;

    for (
        std::size_t i = 1;
        i < segments.size();
        ++i
    ) {
        direction +=
            "->" +
            segments[i].language;
    }

    return direction;
}

std::string escape_json(
    const std::string& value
) {
    std::string result;

    for (
        char character : value
    ) {
        if (character == '\\') {
            result += "\\\\";
        }
        else if (character == '"') {
            result += "\\\"";
        }
        else if (character == '\n') {
            result += "\\n";
        }
        else if (character == '\r') {
            result += "\\r";
        }
        else if (character == '\t') {
            result += "\\t";
        }
        else {
            result += character;
        }
    }

    return result;
}

void print_json(
    const std::string& language,
    bool mixed,
    bool code_switched,
    bool ambiguous,
    double confidence,
    double score_margin,
    int switch_count,
    const std::string& code_switch_direction,
    int english_word_score,
    int filipino_word_score,
    int bisaya_word_score,
    int english_unique_score,
    int filipino_unique_score,
    int bisaya_unique_score,
    double english_trigram_score,
    double filipino_trigram_score,
    double bisaya_trigram_score,
    const std::vector<std::string>& unknown_words,
    const std::vector<LanguageSegment>& segments
) {
    std::cout << "{\n";

    std::cout
        << "  \"language\": \""
        << escape_json(language)
        << "\",\n";

    std::cout
        << "  \"mixed\": "
        << (
            mixed
                ? "true"
                : "false"
        )
        << ",\n";

    std::cout
        << "  \"code_switched\": "
        << (
            code_switched
                ? "true"
                : "false"
        )
        << ",\n";

    std::cout
        << "  \"ambiguous\": "
        << (
            ambiguous
                ? "true"
                : "false"
        )
        << ",\n";

    std::cout
        << "  \"confidence\": "
        << confidence
        << ",\n";

    std::cout
        << "  \"score_margin\": "
        << score_margin
        << ",\n";

    std::cout
        << "  \"switch_count\": "
        << switch_count
        << ",\n";

    std::cout
        << "  \"code_switch_direction\": \""
        << escape_json(
            code_switch_direction
        )
        << "\",\n";

    std::cout
        << "  \"english_word_score\": "
        << english_word_score
        << ",\n";

    std::cout
        << "  \"filipino_word_score\": "
        << filipino_word_score
        << ",\n";

    std::cout
        << "  \"bisaya_word_score\": "
        << bisaya_word_score
        << ",\n";

    std::cout
        << "  \"english_unique_score\": "
        << english_unique_score
        << ",\n";

    std::cout
        << "  \"filipino_unique_score\": "
        << filipino_unique_score
        << ",\n";

    std::cout
        << "  \"bisaya_unique_score\": "
        << bisaya_unique_score
        << ",\n";

    std::cout
        << "  \"english_trigram_score\": "
        << english_trigram_score
        << ",\n";

    std::cout
        << "  \"filipino_trigram_score\": "
        << filipino_trigram_score
        << ",\n";

    std::cout
        << "  \"bisaya_trigram_score\": "
        << bisaya_trigram_score
        << ",\n";

    std::cout
        << "  \"unknown_words\": [";

    for (
        std::size_t i = 0;
        i < unknown_words.size();
        ++i
    ) {
        if (i > 0) {
            std::cout << ", ";
        }

        std::cout
            << "\""
            << escape_json(
                unknown_words[i]
            )
            << "\"";
    }

    std::cout
        << "],\n";

    std::cout
        << "  \"segments\": [";

    for (
        std::size_t i = 0;
        i < segments.size();
        ++i
    ) {
        if (i > 0) {
            std::cout << ", ";
        }

        std::cout << "{";

        std::cout
            << "\"language\": \""
            << escape_json(
                segments[i].language
            )
            << "\", ";

        std::cout
            << "\"words\": \"";

        for (
            std::size_t j = 0;
            j < segments[i].words.size();
            ++j
        ) {
            if (j > 0) {
                std::cout << " ";
            }

            std::cout
                << escape_json(
                    segments[i].words[j]
                );
        }

        std::cout
            << "\"}";

        std::cout << "}";
    }

    std::cout
        << "]\n";

    std::cout << "}\n";
}

int main() {
    std::vector<std::string> english_words = {
        "The weather is nice today.",
        "I am going to school.",
        "The server is working correctly.",
        "Please send me the information.",
        "We are learning something new.",
        "This is a simple English sentence.",
        "The computer is running normally.",
        "I like playing games with my friends.",
        "What are you doing today?",
        "Can you help me with this problem?"
    };

    std::vector<std::string> filipino_words = {
        "Magandang araw sa inyong lahat.",
        "Pupunta ako sa paaralan ngayon.",
        "Kumusta ka ngayong araw?",
        "Ano ang ginagawa mo?",
        "Maraming salamat sa iyong tulong.",
        "Gusto kong matuto ng bagong bagay.",
        "Maayos ang takbo ng computer.",
        "Naglalaro ako kasama ang aking mga kaibigan.",
        "Maaari mo ba akong tulungan?",
        "Masaya akong makipag-usap sa inyo.",
        "Mag-aaral tayo mamaya.",
        "Maglalaro tayo mamaya.",
        "Tayo ay pupunta mamaya.",
        "Mag-aaral ako ngayon.",
        "Tayo ang gagawa nito."
    };

    std::vector<std::string> bisaya_words = {
        "Maayong adlaw kaninyong tanan.",
        "Moadto ko sa eskwelahan karon.",
        "Kumusta ka karong adlawa?",
        "Unsa imong gibuhat?",
        "Daghang salamat sa imong tabang.",
        "Gusto ko makakat-on og bag-ong butang.",
        "Maayo ang dagan sa computer.",
        "Nagdula ko uban sa akong mga higala.",
        "Pwede ba nimo ko tabangan?",
        "Nalipay ko nga makigstorya kaninyo."
    };

    std::map<std::string, std::vector<std::string>> training_files = {
        {
            "english",
            {
                "training/english.txt",
                "training/learned/english.txt"
            }
        },
        {
            "filipino",
            {
                "training/filipino.txt",
                "training/learned/filipino.txt"
            }
        },
        {
            "bisaya",
            {
                "training/bisaya.txt",
                "training/learned/bisaya.txt"
            }
        }
    };

    std::map<
        std::string,
        std::vector<std::string>
    > training_data = {
        {
            "english",
            english_words
        },
        {
            "filipino",
            filipino_words
        },
        {
            "bisaya",
            bisaya_words
        }
    };

    for (
        const auto& language_entry :
        training_files
    ) {
        const std::string& language =
            language_entry.first;

        for (
            const std::string& file_path :
            language_entry.second
        ) {
            std::ifstream file(
                file_path
            );

            if (!file.is_open()) {
                continue;
            }

            std::string line;

            while (
                std::getline(
                    file,
                    line
                )
            ) {
                if (
                    !line.empty()
                ) {
                    training_data[
                        language
                    ].push_back(line);
                }
            }
        }
    }

    std::vector<std::string>
        english_training;

    std::vector<std::string>
        filipino_training;

    std::vector<std::string>
        bisaya_training;

    for (
        const std::string& sentence :
        training_data["english"]
    ) {
        std::vector<std::string> words =
            tokenize(sentence);

        english_training.insert(
            english_training.end(),
            words.begin(),
            words.end()
        );
    }

    for (
        const std::string& sentence :
        training_data["filipino"]
    ) {
        std::vector<std::string> words =
            tokenize(sentence);

        filipino_training.insert(
            filipino_training.end(),
            words.begin(),
            words.end()
        );
    }

    for (
        const std::string& sentence :
        training_data["bisaya"]
    ) {
        std::vector<std::string> words =
            tokenize(sentence);

        bisaya_training.insert(
            bisaya_training.end(),
            words.begin(),
            words.end()
        );
    }

    std::map<std::string, double>
        english_profile =
            build_profile(
                english_training
            );

    std::map<std::string, double>
        filipino_profile =
            build_profile(
                filipino_training
            );

    std::map<std::string, double>
        bisaya_profile =
            build_profile(
                bisaya_training
            );

    std::set<std::string>
        english_vocabulary =
            build_vocabulary(
                english_training
            );

    std::set<std::string>
        filipino_vocabulary =
            build_vocabulary(
                filipino_training
            );

    std::set<std::string>
        bisaya_vocabulary =
            build_vocabulary(
                bisaya_training
            );

    std::cout
        << "Quasar Language Engine v0.7.2.1\n";

    std::cout
        << "English vocabulary: "
        << english_vocabulary.size()
        << "\n";

    std::cout
        << "Filipino vocabulary: "
        << filipino_vocabulary.size()
        << "\n";

    std::cout
        << "Bisaya vocabulary: "
        << bisaya_vocabulary.size()
        << "\n";

    std::cout
        << "Learned vocabulary enabled.\n";

    std::cout
        << "Unknown-word detection enabled.\n";

    std::cout
        << "Enter a message:\n";

    std::string text;

    while (
        std::getline(
            std::cin,
            text
        )
    ) {
        if (text.empty()) {
            continue;
        }

        std::vector<std::string> words =
            tokenize(text);

        if (words.empty()) {
            continue;
        }

        int english_word_score =
            count_vocabulary_matches(
                words,
                english_vocabulary
            );

        int filipino_word_score =
            count_vocabulary_matches(
                words,
                filipino_vocabulary
            );

        int bisaya_word_score =
            count_vocabulary_matches(
                words,
                bisaya_vocabulary
            );

        int english_unique_score =
            count_unique_vocabulary_matches(
                words,
                english_vocabulary,
                filipino_vocabulary,
                bisaya_vocabulary
            );

        int filipino_unique_score =
            count_unique_vocabulary_matches(
                words,
                filipino_vocabulary,
                english_vocabulary,
                bisaya_vocabulary
            );

        int bisaya_unique_score =
            count_unique_vocabulary_matches(
                words,
                bisaya_vocabulary,
                english_vocabulary,
                filipino_vocabulary
            );

        double english_trigram_score = 0.0;
        double filipino_trigram_score = 0.0;
        double bisaya_trigram_score = 0.0;

        for (
            const std::string& word :
            words
        ) {
            english_trigram_score +=
                calculate_trigram_score(
                    word,
                    english_profile
                );

            filipino_trigram_score +=
                calculate_trigram_score(
                    word,
                    filipino_profile
                );

            bisaya_trigram_score +=
                calculate_trigram_score(
                    word,
                    bisaya_profile
                );
        }

        bool english_present =
            english_word_score > 0;

        bool filipino_present =
            filipino_word_score > 0;

        bool bisaya_present =
            bisaya_word_score > 0;

        int present_languages =
            static_cast<int>(
                english_present
            ) +
            static_cast<int>(
                filipino_present
            ) +
            static_cast<int>(
                bisaya_present
            );

        bool mixed =
            present_languages >= 2;

        bool code_switched =
            detect_code_switch(
                english_unique_score,
                filipino_unique_score,
                bisaya_unique_score
            );

        double total_trigram_score =
            english_trigram_score +
            filipino_trigram_score +
            bisaya_trigram_score;

        double highest_trigram_score =
            std::max({
                english_trigram_score,
                filipino_trigram_score,
                bisaya_trigram_score
            });

        double second_highest_trigram_score =
            0.0;

        std::vector<double>
            trigram_scores = {
                english_trigram_score,
                filipino_trigram_score,
                bisaya_trigram_score
            };

        std::sort(
            trigram_scores.begin(),
            trigram_scores.end(),
            std::greater<double>()
        );

        second_highest_trigram_score =
            trigram_scores[1];

        double confidence = 0.0;

        if (
            total_trigram_score > 0.0
        ) {
            confidence =
                highest_trigram_score /
                total_trigram_score;
        }

        double score_margin =
            calculate_score_margin(
                highest_trigram_score,
                second_highest_trigram_score
            );

        bool ambiguous =
            confidence < 0.50 ||
            score_margin < 0.10;

        std::string language =
            "unknown";

        if (ambiguous) {
            language = "ambiguous";
        }
        else if (
            highest_trigram_score ==
            english_trigram_score
        ) {
            language = "english";
        }
        else if (
            highest_trigram_score ==
            filipino_trigram_score
        ) {
            language = "filipino";
        }
        else if (
            highest_trigram_score ==
            bisaya_trigram_score
        ) {
            language = "bisaya";
        }

        if (mixed) {
            if (
                filipino_present &&
                english_present
            ) {
                language = "taglish";
            }
            else {
                language = "mixed";
            }
        }

        std::vector<std::string>
            unknown_words =
                collect_unknown_words(
                    words,
                    english_vocabulary,
                    filipino_vocabulary,
                    bisaya_vocabulary,
                    english_profile,
                    filipino_profile,
                    bisaya_profile
                );

        std::vector<LanguageSegment>
            segments =
                build_language_segments(
                    words,
                    english_vocabulary,
                    filipino_vocabulary,
                    bisaya_vocabulary,
                    english_profile,
                    filipino_profile,
                    bisaya_profile
                );

        int switch_count =
            count_language_switches(
                segments
            );

        std::string code_switch_direction =
            build_switch_direction(
                segments
            );

        print_json(
            language,
            mixed,
            code_switched,
            ambiguous,
            confidence,
            score_margin,
            switch_count,
            code_switch_direction,
            english_word_score,
            filipino_word_score,
            bisaya_word_score,
            english_unique_score,
            filipino_unique_score,
            bisaya_unique_score,
            english_trigram_score,
            filipino_trigram_score,
            bisaya_trigram_score,
            unknown_words,
            segments
        );

        std::cout
            << "Enter a message:\n";
    }

    return 0;
}