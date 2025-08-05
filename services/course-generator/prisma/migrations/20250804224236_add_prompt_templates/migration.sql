-- CreateEnum
CREATE TYPE "public"."PromptCategory" AS ENUM ('COURSE_GENERATION', 'MODULE_GENERATION', 'LESSON_GENERATION', 'SCRIPT_GENERATION', 'SUMMARY_GENERATION', 'CUSTOM');

-- CreateTable
CREATE TABLE "public"."PromptTemplate" (
    "id" TEXT NOT NULL,
    "userId" TEXT,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "category" "public"."PromptCategory" NOT NULL,
    "template" TEXT NOT NULL,
    "variables" JSONB NOT NULL,
    "isPublic" BOOLEAN NOT NULL DEFAULT false,
    "isDefault" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "PromptTemplate_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."PromptUsage" (
    "id" TEXT NOT NULL,
    "templateId" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "courseId" TEXT,
    "variables" JSONB NOT NULL,
    "prompt" TEXT NOT NULL,
    "response" TEXT,
    "tokensUsed" INTEGER,
    "responseTime" INTEGER,
    "success" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "PromptUsage_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "PromptTemplate_userId_idx" ON "public"."PromptTemplate"("userId");

-- CreateIndex
CREATE INDEX "PromptTemplate_category_idx" ON "public"."PromptTemplate"("category");

-- CreateIndex
CREATE INDEX "PromptTemplate_isPublic_idx" ON "public"."PromptTemplate"("isPublic");

-- CreateIndex
CREATE INDEX "PromptTemplate_isDefault_idx" ON "public"."PromptTemplate"("isDefault");

-- CreateIndex
CREATE INDEX "PromptUsage_templateId_idx" ON "public"."PromptUsage"("templateId");

-- CreateIndex
CREATE INDEX "PromptUsage_userId_idx" ON "public"."PromptUsage"("userId");

-- CreateIndex
CREATE INDEX "PromptUsage_createdAt_idx" ON "public"."PromptUsage"("createdAt");

-- AddForeignKey
ALTER TABLE "public"."PromptTemplate" ADD CONSTRAINT "PromptTemplate_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."PromptUsage" ADD CONSTRAINT "PromptUsage_templateId_fkey" FOREIGN KEY ("templateId") REFERENCES "public"."PromptTemplate"("id") ON DELETE CASCADE ON UPDATE CASCADE;
