# File: getjwttoken.rb

class Getjwttoken < Formula
    desc "A tool to securely manage and retrieve JWT tokens"
    homepage "https://github.com/jplonghi/homebrew-tools"
    url "https://github.com/jplonghi/homebrew-tools/blob/main/getjwttoken"
    version "1.0.0"
    sha256 "55f49dc8525b786183efc53a1c626b1538f97b3bb039b4b6b0dcefb1847ce1ee"
  
    def install
      bin.install "getjwttoken"
    end
  
    test do
      system "#{bin}/getjwttoken", "--help"
    end
  end
  